from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Callable

from PIL import Image, UnidentifiedImageError

# что считаем картинками для переименования/конвертации
ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "tif",
    "tiff",
    "webp",
    # намеренно НЕ включаем: psd, svg, raw, heic — Pillow обычно не поддерживает их «из коробки»
}
_INVALID = r'[<>:"/\\|?*\x00-\x1F]'  # запреты Windows + управляющие
_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

log = logging.getLogger("app")


def sanitize_mask(mask: str, fallback: str = "img", max_len: int = 100) -> str:
    s = (mask or "").strip()
    s = re.sub(_INVALID, "_", s)  # запрещённые → _
    s = re.sub(r"\s+", "_", s)  # пробелы-табуляции → _
    s = s.rstrip(" .")  # убираем хвостовые пробелы/точки
    if not s or s.upper() in _RESERVED:
        s = fallback
    return s[:max_len]


def _unique_path(base: Path) -> Path:
    """Если файл существует, добавляем _1, _2, ... пока не станет уникальным."""
    if not base.exists():
        return base
    stem, suf = base.stem, base.suffix
    i = 1
    while True:
        cand = base.with_name(f"{stem}_{i}{suf}")
        if not cand.exists():
            return cand
        i += 1


def rename_and_convert(
    directory: str,
    target_format: str,
    mask: str,
    on_step: Callable[[int, int], None] | None = None,
    create_report: bool = False,
    report_dir: str | Path | None = None,
    config: dict | None = None,  # ← новый параметр
) -> tuple[dict[str, int], Path | None]:
    if config is None:
        config = {}

    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise ValueError(f"{directory} is not a valid directory")

    tf = target_format.lower()
    if tf == "jpg":
        tf = "jpeg"

    files = sorted(p for p in dir_path.iterdir() if p.is_file())
    candidates = [p for p in files if p.suffix[1:].lower() in ALLOWED_EXTENSIONS]
    total = len(candidates)

    stats: dict[str, int] = {"renamed": 0, "converted": 0, "skipped": 0}
    mapping: list[tuple[str, str]] = []

    counter = 1
    log.info("Start convert: dir=%s, format=%s, mask=%s", directory, target_format, mask)
    for idx, src in enumerate(candidates, start=1):
        src_ext = src.suffix[1:].lower()
        if src_ext == "jpg":
            src_ext = "jpeg"

        new_name = f"{mask}{counter:03d}.{tf}"
        dst = _unique_path(dir_path / new_name)

        try:
            if src_ext == tf:
                src.rename(dst)
                stats["renamed"] += 1
                log.info("Renamed: %s -> %s", src.name, dst.name)
            else:
                with Image.open(src) as im:
                    if tf == "jpeg" and im.mode in ("RGBA", "LA", "P"):
                        im = im.convert("RGB")
                    save_kwargs = {}
                    if tf == "jpeg":
                        save_kwargs["quality"] = config.get("jpeg_quality", 92)
                        save_kwargs["optimize"] = config.get("optimize_jpeg", True)
                    im.save(dst, format=tf.upper(), **save_kwargs)

                # удаляем исходник только если keep_originals = False
                if not config.get("keep_originals", False):
                    src.unlink(missing_ok=True)

                log.info("Converted: %s -> %s", src.name, dst.name)
                stats["converted"] += 1

            mapping.append((src.name, dst.name))
            counter += 1

        except (UnidentifiedImageError, OSError) as e:
            stats["skipped"] += 1
            log.warning("Skipped: %s (%s)", src.name, e)
            continue

        if on_step:
            on_step(idx, total)

    # CSV-отчёт
    report_path: Path | None = None
    if create_report and mapping:
        dest = Path(report_dir or config.get("report_dir", dir_path))
        dest.mkdir(parents=True, exist_ok=True)
        report_path = dest / f"rename_report_{datetime.now():%Y%m%d_%H%M%S}.csv"
        with report_path.open("w", encoding="utf-8", newline="") as f:
            f.write("old_name,new_name\n")
            for old, new in mapping:
                f.write(f"{old},{new}\n")

    log.info("Finished. Stats=%s", stats)
    return stats, report_path
