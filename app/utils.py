import re
import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

IMAGE_SIGNATURES = {
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "webp": (b"RIFF",),
}


def clean_text(value, *, upper=False, keep_lines=False):
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    if keep_lines:
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        text = "\n".join(line for line in lines if line)
    else:
        text = re.sub(r"\s+", " ", text)
    return text.upper() if upper else text


def workbook_path():
    for candidate in current_app.config["EXCEL_CANDIDATES"]:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    return None


def save_photo(storage):
    original = secure_filename(storage.filename or "")
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext == "jpeg":
        ext = "jpg"
    header = storage.stream.read(16)
    storage.stream.seek(0)
    signatures = IMAGE_SIGNATURES.get(ext, ())
    if not signatures or not any(header.startswith(sig) for sig in signatures):
        raise ValueError("The file is not a valid JPG, PNG, or WebP image.")
    if ext == "webp" and header[8:12] != b"WEBP":
        raise ValueError("The file is not a valid WebP image.")
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = Path(current_app.config["UPLOAD_FOLDER"])
    folder.mkdir(parents=True, exist_ok=True)
    storage.save(folder / filename)
    return filename


def delete_photo_file(filename):
    if not filename:
        return
    path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    if path.is_file():
        path.unlink()
