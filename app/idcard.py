"""Stamp registry values onto the motorela ID artwork.

The template page is larger than the card. The card itself is 5.5 by 8.5
inches, which is exactly half of a letter sheet in landscape. Each printed
page is letter landscape, with one card on the left half and, for bulk
printing, a second card on the right half. The artwork is placed unchanged. Blank fields are filled from the
registry, and a saved portrait replaces the blue photo box.
"""

import os
from io import BytesIO
from pathlib import Path

import fitz
from flask import current_app
from PIL import Image, ImageDraw, UnidentifiedImageError

CARD_CLIP = fitz.Rect(108, 162, 504, 774)
CARD_WIDTH = 396
CARD_HEIGHT = 612
PAGE_WIDTH = 792
PAGE_HEIGHT = 612

# Card-relative points, origin at the top-left of the artwork.
# Values sit on the template rules and stay clear of the printed captions.
FIELDS = {
    "id_no": {"x0": 248, "x1": 380, "baseline": 165.5, "size": 20, "align": "left", "keep_size": True},
    "valid": {"x0": 304, "x1": 382, "baseline": 207.5, "size": 20, "align": "left", "keep_size": True},
    "cab": {"x0": 200, "x1": 382, "baseline": 270.0, "size": 30, "align": "center"},
    "driver": {"x0": 16, "x1": 380, "baseline": 344.0, "size": 45, "align": "center"},
    "address": {"x0": 16, "x1": 380, "baseline": 416.0, "size": 30, "align": "center"},
}

# Open space under the ADDRESS caption, above the mayor's signature.
ASSOCIATION = {"x0": 20, "x1": 376, "baseline": 490, "size": 30, "align": "center"}
MEMBER_LINE = {"x0": 20, "x1": 376, "baseline": 516, "size": 14, "align": "center"}

# Blue portrait box on the template, card-relative points.
PHOTO = fitz.Rect(20.63, 112.19, 164.63, 256.19)
PHOTO_RADIUS = 5.3
PHOTO_PX = 640

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
]


def template_path():
    for candidate in current_app.config["ID_TEMPLATE_CANDIDATES"]:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def _font_file():
    for candidate in FONT_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return None


def _fit(font, text, width, size, minimum=6.5):
    while size > minimum and font.text_length(text, fontsize=size) > width:
        size -= 0.25
    return size


def _draw(page, font, origin, spec, text):
    text = " ".join((text or "").split())
    if not text:
        return
    width = spec["x1"] - spec["x0"]
    size = spec["size"]
    length = font.text_length(text, fontsize=size)
    squeeze = 1
    if length > width:
        if spec.get("keep_size"):
            squeeze = width / length
        else:
            size = _fit(font, text, width, size)
            length = font.text_length(text, fontsize=size)
    if spec["align"] == "center":
        x = spec["x0"] + max(0, (width - length * squeeze) / 2)
    else:
        x = spec["x0"]
    point = fitz.Point(origin.x + x, origin.y + spec["baseline"])
    page.insert_text(
        point,
        text,
        fontname="idface",
        fontsize=size,
        color=(0, 0, 0),
        morph=(point, fitz.Matrix(squeeze, 1)),
    )


def _values(member):
    year = member.record_year or ""
    return {
        "id_no": member.franchise_number,
        "valid": f"01 JAN {year}" if year else "",
        "cab": member.body_number,
        "driver": member.driver_display,
        "address": member.address,
    }


def _photo_stream(path):
    image = Image.open(path).convert("RGB")
    width, height = image.size
    side = PHOTO_PX
    scale = max(side / width, side / height)
    resized = (
        max(side, round(width * scale)),
        max(side, round(height * scale)),
    )
    image = image.resize(resized, Image.Resampling.LANCZOS)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side)).convert("RGBA")
    mask = Image.new("L", image.size, 0)
    radius = PHOTO_RADIUS / PHOTO.width * side
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, side - 1, side - 1), radius=radius, fill=255)
    image.putalpha(mask)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _place_photo(page, origin, member):
    filename = member.photo_filename
    if not filename:
        return
    path = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    if not path.is_file():
        return
    try:
        stream = _photo_stream(path)
    except (OSError, UnidentifiedImageError, ValueError):
        return
    box = fitz.Rect(
        PHOTO.x0 + origin.x,
        PHOTO.y0 + origin.y,
        PHOTO.x1 + origin.x,
        PHOTO.y1 + origin.y,
    )
    page.insert_image(box, stream=stream, keep_proportion=False)


def _stamp(page, font, origin, member):
    _place_photo(page, origin, member)
    for key, value in _values(member).items():
        _draw(page, font, origin, FIELDS[key], value)
    association = " ".join((member.association or "").split())
    if association:
        _draw(page, font, origin, ASSOCIATION, association)
        _draw(page, font, origin, MEMBER_LINE, "MEMBER")


def build_id_pdf(members):
    source_path = template_path()
    if not source_path:
        raise FileNotFoundError("ID template PDF was not found.")
    font_file = _font_file()
    if not font_file:
        raise FileNotFoundError("A bold font for the ID overlay was not found.")

    font = fitz.Font(fontfile=font_file)
    source = fitz.open(source_path)
    output = fitz.open()
    try:
        slots = (
            fitz.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT),
            fitz.Rect(CARD_WIDTH, 0, PAGE_WIDTH, CARD_HEIGHT),
        )
        page = None
        for index, member in enumerate(members):
            slot = index % 2
            if slot == 0:
                page = output.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
                page.insert_font(fontname="idface", fontfile=font_file)
            origin = fitz.Point(slots[slot].x0, slots[slot].y0)
            page.show_pdf_page(slots[slot], source, 0, clip=CARD_CLIP)
            _stamp(page, font, origin, member)
        output.set_metadata(
            {
                "title": "Motorela operator ID",
                "author": "Municipality of Jagna",
            }
        )
        return output.tobytes(deflate=True, garbage=3)
    finally:
        source.close()
        output.close()


def download_name(members):
    if len(members) == 1:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in members[0].body_number)
        return f"motorela-id-{safe or 'card'}.pdf"
    return "motorela-ids.pdf"
