
""" 
Module/Script Name: qr_watermark.py

Description:
Batch watermarks all images in the input directory with a generated QR code (top-left)
and a styled text overlay (bottom-left), with auto-scaling and 5% vertical padding.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-14

Last Modified Date:
2025-04-14

Comments:
- v1.00: Initial QR watermark implementation
- v1.01: Added text overlay with Playfair Display and drop shadow
- v1.02: Auto-scales text to fit image, moved QR to top-left
- v1.03: Added 5% vertical padding below text overlay
"""

import os
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from glob import glob

# === CONFIGURATION ===
INPUT_DIR = 'input_images'
OUTPUT_DIR = 'output_images'
QR_LINK = 'https://yourwebsite.com/free-quote'
QR_SIZE_RATIO = 0.15
QR_OPACITY = 0.85
TEXT_OVERLAY = "Salvo Metal Works – Custom Architectural Metal Fabrication"
TEXT_COLOR = (250, 249, 246)  # Antique White
SHADOW_COLOR = (0, 0, 0, 128)  # Semi-transparent black
TEXT_POSITION = 'bottom-left'
FONT_SIZE_RATIO = 0.035  # Initial guess

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Generate QR code
def generate_qr_code(link):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return qr_img

# Add QR and text overlay
def add_watermarks(image_path, qr_img, font_path='PlayfairDisplay-Regular.ttf'):
    img = Image.open(image_path).convert("RGBA")
    img_w, img_h = img.size

    # Resize QR
    qr_size = int(img_w * QR_SIZE_RATIO)
    qr_resized = qr_img.resize((qr_size, qr_size))

    # Adjust QR opacity
    alpha = qr_resized.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(QR_OPACITY)
    qr_resized.putalpha(alpha)

    # Paste QR (top-left corner)
    qr_x = 10
    qr_y = 10
    img.paste(qr_resized, (qr_x, qr_y), qr_resized)

    # Draw text
    draw = ImageDraw.Draw(img)
    max_width = img_w - 20
    font_size = int(img_w * FONT_SIZE_RATIO)

    # Auto-scale font to fit within width
    while font_size > 10:
        font = ImageFont.truetype(font_path, font_size)
        bbox = draw.textbbox((0, 0), TEXT_OVERLAY, font=font)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width:
            break
        font_size -= 1

    text_h = bbox[3] - bbox[1]
    text_x = 10
    padding_bottom = int(img_h * 0.05)
    text_y = img_h - text_h - padding_bottom

    # Drop shadow
    draw.text((text_x + 2, text_y + 2), TEXT_OVERLAY, font=font, fill=SHADOW_COLOR)
    # Foreground
    draw.text((text_x, text_y), TEXT_OVERLAY, font=font, fill=TEXT_COLOR)

    return img.convert("RGB")

# Run batch
def main():
    qr_image = generate_qr_code(QR_LINK)
    for filepath in glob(f"{INPUT_DIR}/*.*"):
        try:
            result = add_watermarks(filepath, qr_image)
            output_filename = os.path.basename(filepath)
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            result.save(output_path, "JPEG", quality=85)
            print(f"✅ Watermarked: {output_filename}")
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")

if __name__ == "__main__":
    main()
