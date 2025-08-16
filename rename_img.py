# -*- coding: utf-8 -*-
"""
Module/Script Name: rename_img.py

Description:
Generates short, SEO-friendly filenames from noisy/long originals.
Drop-in for qr_watermark.py → seo_friendly_name(stem) → "<slug>.jpg".

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-08-16

Last Modified Date:
2025-08-16

Comments:
- v1.01: Heuristic slug generator (noise stripping, dedupe, slugify).
"""

import os
import re
from typing import Iterable, List, Set

_SEPARATORS = re.compile(r"[ \t\-\._,+]+")
_NON_ALNUM = re.compile(r"[^a-z0-9\-]+")

_STRIP_PATTERNS = [
    re.compile(r"\b\d{2,5}\s*[xX]\s*\d{2,5}\b"),                      # 1200x800
    re.compile(r"\b(?:19|20)\d{2}[-_\/]?\d{1,2}[-_\/]?\d{1,2}\b"),   # 2025-08-16 / 20250816
    re.compile(r"\b\d{1,2}[-_\/]\d{1,2}[-_\/]\b(?:19|20)\d{2}\b"),  # 08-16-2025
    re.compile(r"\b(?:19|20)\d{2}\b"),                                   # lone year
    re.compile(r"\b\d{1,2}[-:.]\d{2}[-:.]\d{2}\b"),                    # 12-34-56
    re.compile(r"\b[a-f0-9]{8,}\b", re.IGNORECASE),                       # long hex/hash
    re.compile(r"[\(\[\{][^\)\]\}]{0,50}[\)\]\}]"),                # bracketed notes
]

_STOPWORDS: Set[str] = {
    "img", "imgp", "dsc", "pxl", "psx", "gopr", "pano", "panorama",
    "screenshot", "screen", "shot", "edited", "edit", "final", "final2",
    "copy", "new", "version", "v2", "v3", "v4", "hdr", "raw", "heic",
    "android", "iphone", "canon", "nikon", "sony", "fujifilm", "olympus",
    "lumix", "leica", "export", "resized", "compressed", "large",
    "medium", "small", "original", "orig", "draft", "highres",
    "penzenmaster"
}

def _strip_noise(s: str) -> str:
    for pat in _STRIP_PATTERNS:
        s = pat.sub(" ", s)
    return s

def _tokenize(stem: str) -> List[str]:
    s = _strip_noise(stem.lower())
    return [p for p in _SEPARATORS.split(s) if p]

def _is_meaningful(tok: str, min_len: int = 3) -> bool:
    if len(tok) < min_len:
        return False
    if tok in _STOPWORDS:
        return False
    if tok.isdigit():
        return False
    letters = sum(c.isalpha() for c in tok)
    digits  = sum(c.isdigit() for c in tok)
    return letters >= digits

def _dedupe(tokens: Iterable[str]) -> List[str]:
    seen, out = set(), []
    for t in tokens:
        if t not in seen:
            out.append(t); seen.add(t)
    return out

def _slugify(parts: Iterable[str]) -> str:
    s = "-".join(parts)
    s = _NON_ALNUM.sub("-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")

def seo_friendly_name(original_name: str) -> str:
    """
    Accepts a filename *stem* (no extension) and returns '<slug>.jpg'.
    """
    tokens = _tokenize(original_name)
    tokens = [t for t in tokens if _is_meaningful(t)]
    tokens = _dedupe(tokens)

    slug = _slugify(tokens[:6]) or "image"
    return f"{slug}.jpg"

# Optional utility for batch renaming a directory (not used by GUI flow).
def rename_images(directory: str) -> None:
    for filename in os.listdir(directory):
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            stem, _ext = os.path.splitext(filename)
            new_name = seo_friendly_name(stem)
            src = os.path.join(directory, filename)
            dst = os.path.join(directory, new_name)
            # avoid accidental overwrite
            base, ext = os.path.splitext(dst)
            i = 2
            candidate = dst
            while os.path.exists(candidate):
                candidate = f"{base}-{i}{ext}"
                i += 1
            os.rename(src, candidate)
            print(f'Renamed "{filename}" -> "{os.path.basename(candidate)}"')
