"""
Module/Script Name: qr_watermark.py

Description:
Applies a QR code watermark and styled text overlay to images in the input directory,
using settings from a JSON configuration file.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-14

Last Modified Date:
2025-04-14

Comments:
- v1.05 β: Externalized config parameters into JSON file for easier control and UI integration
"""

import os
import qrcode
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance


# === CONFIG LOADER ===
def load_config(path="config/settings.json"):
    with open(path, "r") as f:
        return json.load(f)


config = load_config()

# === CONFIGURATION ===
INPUT_DIR = config["input_dir"]
OUTPUT_DIR = config["output_dir"]
QR_LINK = config["qr_link"]
QR_SIZE_RATIO = config["qr_size_ratio"]
QR_OPACITY = config["qr_opacity"]
TEXT_OVERLAY = config["text_overlay"]
TEXT_COLOR = tuple(config["text_color"])
SHADOW_COLOR = tuple(config["shadow_color"])
FONT_SIZE_RATIO = config["font_size_ratio"]
TEXT_PADDING_BOTTOM_RATIO = config["text_padding_bottom_ratio"]
QR_PADDING_VH_RATIO = config["qr_padding_vh_ratio"]


# === MAIN SCRIPT ===
def generate_qr_code(link, size):
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return qr_img.resize(size, Image.LANCZOS)


def apply_watermark(image_path):
    try:
        base_img = Image.open(image_path).convert("RGBA")
        width, height = base_img.size

        # --- Generate QR Code ---
        qr_size = int(height * QR_SIZE_RATIO)
        qr_img = generate_qr_code(QR_LINK, (qr_size, qr_size))
        qr_img.putalpha(int(255 * QR_OPACITY))

        # Position: upper-right
        qr_padding = int(height * QR_PADDING_VH_RATIO)
        qr_position = (width - qr_size - qr_padding, qr_padding)
        base_img.paste(qr_img, qr_position, qr_img)

        # --- Add Text Overlay ---
        draw = ImageDraw.Draw(base_img)
        font_size = int(width * FONT_SIZE_RATIO)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        # Dynamic multiline text handling
        lines = TEXT_OVERLAY.splitlines()
        max_line_width = max(draw.textlength(line, font=font) for line in lines)
        total_height = sum(
            font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines
        )
        text_x = 10
        text_y = height - int(height * TEXT_PADDING_BOTTOM_RATIO) - total_height

        for line in lines:
            # Drop shadow
            draw.text((text_x + 2, text_y + 2), line, font=font, fill=SHADOW_COLOR)
            draw.text((text_x, text_y), line, font=font, fill=TEXT_COLOR)
            text_y += font.getbbox(line)[3] - font.getbbox(line)[1]

        # --- Save Output ---
        output_path = os.path.join(OUTPUT_DIR, os.path.basename(image_path))
        base_img.convert("RGB").save(output_path, "JPEG")
        print(f"✅ Processed: {output_path}")
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            apply_watermark(os.path.join(INPUT_DIR, filename))


if __name__ == "__main__":
    main()
