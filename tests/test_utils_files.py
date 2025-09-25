from pathlib import Path

from PIL import Image

from utils.files import (
    rename_and_convert,
    sanitize_mask,
)

# ---------- helpers ----------


def make_image(path: Path, mode="RGB", size=(4, 4), color=(255, 0, 0)):
    """Создаёт маленькую картинку нужного формата по расширению файла."""
    fmt = path.suffix[1:].lower()
    if fmt == "jpg":
        fmt = "jpeg"
    img = Image.new(mode, size, color)
    save_kwargs = {}
    if fmt == "jpeg":
        save_kwargs = {"quality": 92, "optimize": True}
    img.save(path, format=fmt.upper(), **save_kwargs)


# ---------- sanitize_mask ----------


def test_sanitize_mask_basic():
    assert sanitize_mask("My: mask*2025") == "My__mask_2025"
    assert sanitize_mask(" name  with   spaces ") == "name_with_spaces"


def test_sanitize_mask_reserved_to_fallback():
    # CON/PRN/COM1 и т.п. → fallback 'img'
    assert sanitize_mask("CON") == "img"
    assert sanitize_mask("  ") == "img"
    assert sanitize_mask("name.") == "name"  # хвостовые точки/пробелы убираем


# ---------- rename_and_convert ----------


def test_convert_png_to_jpeg(tmp_path: Path):
    src = tmp_path / "a.png"
    make_image(src, mode="RGB")
    stats, report = rename_and_convert(str(tmp_path), "JPG", "img", create_report=False)
    # конвертация произошла
    assert stats["converted"] == 1 and stats["renamed"] == 0 and stats["skipped"] == 0
    # имя по маске и расширение .jpeg (мы унифицируем JPG→JPEG)
    assert (tmp_path / "img001.jpeg").exists()
    assert report is None


def test_rename_only_when_same_format(tmp_path: Path):
    src = tmp_path / "x.jpeg"
    make_image(src, mode="RGB")
    stats, _ = rename_and_convert(str(tmp_path), "JPG", "mask", create_report=False)
    # формат совпал → только переименование
    assert stats["renamed"] == 1 and stats["converted"] == 0
    assert (tmp_path / "mask001.jpeg").exists()


def test_rgba_png_to_jpeg_drops_alpha(tmp_path: Path):
    src = tmp_path / "rgba.png"
    make_image(src, mode="RGBA")  # с альфой
    stats, _ = rename_and_convert(str(tmp_path), "JPG", "m", create_report=False)
    out = tmp_path / "m001.jpeg"
    assert out.exists()
    # JPEG не имеет альфы → должен быть RGB
    with Image.open(out) as im:
        assert im.mode == "RGB"
    assert stats["converted"] == 1


def test_no_supported_files(tmp_path: Path):
    # создаём несSupported расширения → .txt и .svg
    (tmp_path / "a.txt").write_text("dummy", encoding="utf-8")
    (tmp_path / "b.svg").write_text("<svg/>", encoding="utf-8")
    stats, report = rename_and_convert(str(tmp_path), "PNG", "x", create_report=False)
    # функция фильтрует кандидатов по ALLOWED_EXTENSIONS → ничего не обработано
    assert stats["converted"] == 0 and stats["renamed"] == 0 and stats["skipped"] == 0
    assert report is None


def test_collision_creates_increment_suffix(tmp_path: Path):
    # заранее кладём целевое имя, чтобы вызвать коллизию
    (tmp_path / "img001.jpeg").write_bytes(b"stub")
    # теперь создаём JPEG, который при rename даст то же имя
    src = tmp_path / "source.jpeg"
    make_image(src)
    stats, _ = rename_and_convert(str(tmp_path), "JPG", "img", create_report=False)
    # из-за коллизии должен появиться img001_1.jpeg
    assert (tmp_path / "img001_1.jpeg").exists()
    assert (tmp_path / "img002.jpeg").exists()
    assert stats["renamed"] == 2


def test_report_created_when_enabled(tmp_path: Path):
    # два файла → две записи в отчёте
    make_image(tmp_path / "a.png")
    make_image(tmp_path / "b.png")
    report_dir = tmp_path / "_reports"
    stats, report = rename_and_convert(
        str(tmp_path), "JPG", "m", create_report=True, report_dir=report_dir
    )
    assert stats["converted"] == 2
    assert report is not None and report.exists()
    lines = report.read_text(encoding="utf-8").strip().splitlines()
    # заголовок + 2 строки
    assert len(lines) == 1 + 2
