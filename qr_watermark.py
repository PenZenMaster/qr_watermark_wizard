"""
Module/Script Name: qr_watermark.py

Description:
Applies a QR code watermark and styled text overlay to images in the input directory,
using settings from a JSON configuration file. Supports in-memory preview mode.

Author(s):
George Penzenik - Rank Rocket Co

Created Date:
04-14-2025

Last Modified Date:
08-01-2025

Version:
v1.07.15

Comments:
- v1.07.14: Fixed output file extensions - PNG inputs now properly save as .jpg files.
- v1.07.15: Added SEO-friendly filename option.
"""

from typing import Optional
import os
import qrcode
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from rename_img import seo_friendly_name

def ensure_unique_path(path: str, strategy: str = "counter") -> str:
    """
    If 'path' exists, append -2, -3, ... (counter) or a -YYYYMMDDHHMMSS (timestamp).
    """
    import os
    import time
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    if strategy == "timestamp":
        ts = time.strftime("%Y%m%d%H%M%S")
        candidate = f"{base}-{ts}{ext}"
        # If still collides, fall back to counter
        if not os.path.exists(candidate):
            return candidate
    # counter fallback
    n = 2
    candidate = f"{base}-{n}{ext}"
    while os.path.exists(candidate):
        n += 1
        candidate = f"{base}-{n}{ext}"
    return candidate



def load_config(path="config/settings.json"):  # noqa: C901
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def refresh_config(path="config/settings.json"):  # noqa: C901
    global config, INPUT_DIR, OUTPUT_DIR, QR_LINK, QR_SIZE_RATIO, QR_OPACITY, TEXT_OVERLAY, TEXT_COLOR, SHADOW_COLOR, FONT_SIZE_RATIO, TEXT_PADDING_BOTTOM_RATIO, QR_PADDING_VH_RATIO, SEO_RENAME, COLLISION_STRATEGY, PROCESS_RECURSIVE, SLUG_MAX_WORDS, SLUG_MIN_LEN, SLUG_STOPWORDS, SLUG_WHITELIST, SLUG_PREFIX, SLUG_LOCATION
    config = load_config(path)
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
    SEO_RENAME = config.get("seo_rename", False)
    COLLISION_STRATEGY = config.get("collision_strategy", "counter")
    PROCESS_RECURSIVE = config.get("process_recursive", False)
    SLUG_MAX_WORDS = int(config.get("slug_max_words", 6))
    SLUG_MIN_LEN = int(config.get("slug_min_len", 3))
    SLUG_STOPWORDS = config.get("slug_stopwords", [])
    SLUG_WHITELIST = config.get("slug_whitelist", [])
    SLUG_PREFIX = config.get("slug_prefix", "")
    SLUG_LOCATION = config.get("slug_location", "")
    # Apply slug configuration to rename_img
    try:
        import rename_img
        rename_img.configure_slug(
            max_words=SLUG_MAX_WORDS,
            min_len=SLUG_MIN_LEN,
            stopwords=SLUG_STOPWORDS,
            whitelist=SLUG_WHITELIST,
            prefix=SLUG_PREFIX,
            location=SLUG_LOCATION,
        )
    except Exception as _cfg_err:
        print(f"[WARN] Could not configure slug module: {_cfg_err}")


# Load initial config
config = load_config()
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
SEO_RENAME = config.get("seo_rename", False)

# Additional runtime settings with defaults
COLLISION_STRATEGY = config.get("collision_strategy", "counter")
PROCESS_RECURSIVE = config.get("process_recursive", False)
SLUG_MAX_WORDS = int(config.get("slug_max_words", 6))
SLUG_MIN_LEN = int(config.get("slug_min_len", 3))
SLUG_STOPWORDS = config.get("slug_stopwords", [])
SLUG_WHITELIST = config.get("slug_whitelist", [])
SLUG_PREFIX = config.get("slug_prefix", "")
SLUG_LOCATION = config.get("slug_location", "")
try:
    import rename_img
    rename_img.configure_slug(
        max_words=SLUG_MAX_WORDS,
        min_len=SLUG_MIN_LEN,
        stopwords=SLUG_STOPWORDS,
        whitelist=SLUG_WHITELIST,
        prefix=SLUG_PREFIX,
        location=SLUG_LOCATION,
    )
except Exception as _cfg_err:
    print(f"[WARN] Could not configure slug module at import time: {_cfg_err}")


def generate_qr_code(link, size):
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")  # type: ignore
    return qr_img.resize(size, Image.Resampling.LANCZOS)


def apply_watermark(image_path, return_image=False, out_dir: Optional[str] = None):  # noqa: C901
    # Ensure config is current
    refresh_config()
    try:
        orig = Image.open(image_path)
        exif_bytes = orig.info.get("exif")
        icc_profile = orig.info.get("icc_profile")
        base_img = orig.convert("RGBA")
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
        lines = TEXT_OVERLAY.splitlines()
        total_height = sum(
            font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines
        )
        text_x = 10
        text_y = height - int(height * TEXT_PADDING_BOTTOM_RATIO) - total_height
        for line in lines:
            draw.text((text_x + 2, text_y + 2), line, font=font, fill=SHADOW_COLOR)
            draw.text((text_x, text_y), line, font=font, fill=TEXT_COLOR)
            text_y += font.getbbox(line)[3] - font.getbbox(line)[1]
        if return_image:
            return base_img.convert("RGB")
        # --- Save Output ---
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Generate output filename
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        if SEO_RENAME:
            # Use SEO-friendly naming
            output_filename = seo_friendly_name(base_filename)
        else:
            # Use original filename with .jpg extension
            output_filename = f"{base_filename}.jpg"
        dest_dir = out_dir if out_dir else OUTPUT_DIR
        os.makedirs(dest_dir, exist_ok=True)
        output_path = ensure_unique_path(os.path.join(dest_dir, output_filename), strategy=COLLISION_STRATEGY)

        save_kwargs = {"quality": 92, "optimize": True, "progressive": True}
        if exif_bytes:
            save_kwargs["exif"] = exif_bytes
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile
        base_img.convert("RGB").save(output_path, "JPEG", **save_kwargs)
        print(f"[SUCCESS] Processed: {output_path}")
    except Exception as e:
        error_msg = f"[ERROR] Error processing {image_path}: {e}"
        print(error_msg)
        if return_image:
            return None


def main():
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        processed_count = 0
        error_count = 0

        print(f"Starting watermark processing...")
        print(f"Input directory: {INPUT_DIR}")
        print(f"Output directory: {OUTPUT_DIR}")

        for filename in os.listdir(INPUT_DIR):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                try:
                    apply_watermark(os.path.join(INPUT_DIR, filename))
                    processed_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"[ERROR] Failed to process {filename}: {e}")

        print(f"\nProcessing complete!")
        print(f"Successfully processed: {processed_count} images")
        if error_count > 0:
            print(f"Errors encountered: {error_count} images")

    except Exception as e:
        print(f"[CRITICAL ERROR] {e}")


if __name__ == "__main__":
    main()