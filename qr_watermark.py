"""
Module/Script Name: qr_watermark.py

Description:
Batch watermarks all images in the input directory with a generated QR code linking to a given URL.

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-04-14

Last Modified Date:
2025-04-14

Comments:
- v1.00: Initial version. Batch watermarking with QR overlay, bottom-right placement.
"""

import os
import qrcode
from PIL import Image, ImageEnhance
from glob import glob

# --- Configuration ---
INPUT_DIR = "input_images"
OUTPUT_DIR = "output_images"
QR_LINK = "https://salvometalworks.com/"  # UPDATE THIS
QR_SIZE_RATIO = 0.15  # QR will be 15% of image width
QR_OPACITY = 0.85  # Opacity from 0.0 to 1.0
QR_POSITION = "bottom-right"  # Options: 'bottom-right', 'top-left', etc.


# --- Generate QR Code ---
def generate_qr_code(link):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(link)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img_qr


# --- Apply Watermark ---
def add_qr_watermark(base_image, qr_image, position="bottom-right", opacity=0.85):
    base = base_image.convert("RGBA")
    qr_w, qr_h = qr_image.size
    img_w, img_h = base.size

    positions = {
        "bottom-right": (img_w - qr_w - 10, img_h - qr_h - 10),
        "top-left": (10, 10),
        "top-right": (img_w - qr_w - 10, 10),
        "bottom-left": (10, img_h - qr_h - 10),
        "center": ((img_w - qr_w) // 2, (img_h - qr_h) // 2),
    }
    pos = positions.get(position, (img_w - qr_w - 10, img_h - qr_h - 10))

    # Adjust opacity
    qr_image = qr_image.copy()
    alpha = qr_image.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    qr_image.putalpha(alpha)

    # Composite images
    base.paste(qr_image, pos, qr_image)
    return base.convert("RGB")


# --- Main Batch Runner ---
def batch_watermark_images():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    qr = generate_qr_code(QR_LINK)

    for filepath in glob(f"{INPUT_DIR}/*.*"):
        try:
            img = Image.open(filepath)
            img_w, img_h = img.size

            qr_scaled = qr.resize(
                (int(img_w * QR_SIZE_RATIO), int(img_w * QR_SIZE_RATIO))
            )
            watermarked = add_qr_watermark(img, qr_scaled, QR_POSITION, QR_OPACITY)

            filename = os.path.basename(filepath)
            output_path = os.path.join(OUTPUT_DIR, filename)
            watermarked.save(output_path, "JPEG", quality=85)

            print(f"✅ Watermarked: {filename}")
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")


if __name__ == "__main__":
    batch_watermark_images()
