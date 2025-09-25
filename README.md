# 🖼️ Image Converter

A simple desktop application for batch converting and renaming images, built with Python and Flet.

---

## 🚀 Features

- Convert images into popular formats (**JPG/JPEG**, **PNG**, **WEBP**, **TIFF**, **GIF**).
- Safe renaming with a user-defined filename mask (`mask001.jpg`, `mask002.jpg` …).
- Automatic handling of duplicate names (adds `_copy`, `_copy2`).
- Mask sanitizer: removes invalid characters for safe filenames.
- Real-time progress and notifications.
- Error handling and skipped file logging.
- Clean and minimalist interface.

---

## 🛠 Technologies

- Python 3.13
- [Flet](https://flet.dev/) — for GUI
- [Pillow](https://python-pillow.org/) — for image conversion
- PyInstaller — for exe builds
- Pytest + Coverage — for testing
- Ruff + Black — for linting and formatting

---

## ⚙️ How to Run

1. Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/Image-Converter.git
cd Image-Converter
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python main.py
```

## 📸 Screenshots
Main window

![Main window](assets/screensots/app.jpg)

## 📦 Download
You can download the latest .exe build from the Releases page.

## 📫 Contacts

- Telegram: @Alex_Gicheva
- Email: alexgicheva@gmail.com

✨ Thank you for using Image Converter! We hope it saves you time and effort.
