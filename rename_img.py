# -*- coding: utf-8 -*-
"""
Module/Script Name: rename_img.py

Description:
Generates short, SEO-friendly filenames from noisy/long originals.
Drop-in for qr_watermark.py → seo_friendly_name(stem) → "<slug>.jpg".
Supports runtime configuration via configure_slug().

Author(s):
Skippy the Magnificent with an eensy weensy bit of help from that filthy monkey, Big G

Created Date:
2025-08-16

Last Modified Date:
2025-08-16

Comments:
- v1.02: Configurable slug params + whitelist/prefix/location injection.
"""

import os
import re
from typing import Iterable, List, Set, Optional

# --- Runtime-tunable parameters (set via configure_slug) ---
SLUG_MAX_WORDS: int = 6
SLUG_MIN_LEN: int = 3
STOPWORDS_EXTRA: Set[str] = set()
WHITELIST: Set[str] = set()
PREFIX_TOKENS: List[str] = []
LOCATION_TOKENS: List[str] = []

_SEPARATORS = re.compile(r"[ \t\-\._,+]+")
_NON_ALNUM = re.compile(r"[^a-z0-9\-]+")

_STRIP_PATTERNS = [
    re.compile(r"\b\d{2,5}\s*[xX]\s*\d{2,5}\b"),                      # 1200x800
    re.compile(r"\b(?:19|20)\d{2}[-_\/]?\d{1,2}[-_\/]?\d{1,2}\b"),   # 2025-08-16 / 20250816
    re.compile(r"\b\d{1,2}[-_\/]\d{1,2}[-_\/]\b(?:19|20)\d{2}\b"),  # 08-16-2025
    re.compile(r"\b(?:19|20)\d{2}\b"),                                   # lone year
    re.compile(r"\b\d{1,2}[-:.]\d{2}[-:.]\d{2}\b"),                    # 12-34-56
    re.compile(r"\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b", re.IGNORECASE),  # UUID format
    re.compile(r"\b[a-f0-9]{4}-[a-f0-9]{4,12}\b", re.IGNORECASE),     # UUID fragments like 2c8d-c4a04fee26cb
    re.compile(r"\b[a-f0-9]{8,}\b", re.IGNORECASE),                       # long hex/hash (catches 8+ chars including c4a04fee26cb)
    re.compile(r"[\(\[\{][^\)\]\}]{0,50}[\)\]\}]"),                # bracketed notes
    re.compile(r"[-_]\d+$"),                                          # trailing numbers like -0, _1, etc.
]

# Built-in junk
_STOPWORDS_BUILTIN: Set[str] = {
    "img","imgp","dsc","pxl","psx","gopr","pano","panorama",
    "screenshot","screen","shot","edited","edit","final","final2",
    "copy","new","version","v2","v3","v4","hdr","raw","heic",
    "android","iphone","canon","nikon","sony","fujifilm","olympus",
    "lumix","leica","export","resized","compressed","large",
    "medium","small","original","orig","draft","highres",
    "penzenmaster"
}

def _strip_noise(s: str) -> str:
    for pat in _STRIP_PATTERNS:
        s = pat.sub(" ", s)
    return s

def _tokenize(stem: str) -> List[str]:
    s = _strip_noise(stem.lower())
    return [p for p in _SEPARATORS.split(s) if p]

def _is_meaningful(tok: str, min_len: int) -> bool:
    if len(tok) < min_len:
        return False
    if tok in _STOPWORDS_BUILTIN or tok in STOPWORDS_EXTRA:
        return False
    if WHITELIST and tok not in WHITELIST:
        return False
    if tok.isdigit():
        return False
    # Filter out hex strings (8+ chars of hex characters)
    if len(tok) >= 8 and re.match(r'^[a-f0-9]+$', tok, re.IGNORECASE):
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

def _slug_tokens_from_name(original_name: str) -> List[str]:
    tokens = _tokenize(original_name)
    tokens = [t for t in tokens if _is_meaningful(t, SLUG_MIN_LEN)]
    tokens = _dedupe(tokens)
    # Prepend configured prefix/location tokens (dedupe-preserving order)
    base: List[str] = []
    for block in (PREFIX_TOKENS, LOCATION_TOKENS):
        for t in block:
            if t and t not in base:
                base.append(t)
    for t in tokens:
        if t not in base:
            base.append(t)
    return base[:SLUG_MAX_WORDS]

def seo_friendly_name(original_name: str) -> str:
    """Accepts a filename *stem* (no extension) and returns '<slug>.jpg'."""
    slug = _slugify(_slug_tokens_from_name(original_name)) or "image"
    return f"{slug}.jpg"

def configure_slug(
    max_words: Optional[int] = None,
    min_len: Optional[int] = None,
    stopwords: Optional[Iterable[str]] = None,
    whitelist: Optional[Iterable[str]] = None,
    prefix: Optional[str] = None,
    location: Optional[str] = None,
) -> None:
    """Configure slug generation at runtime (safe to call repeatedly)."""
    global SLUG_MAX_WORDS, SLUG_MIN_LEN, STOPWORDS_EXTRA, WHITELIST, PREFIX_TOKENS, LOCATION_TOKENS
    if max_words is not None:
        SLUG_MAX_WORDS = int(max_words)
    if min_len is not None:
        SLUG_MIN_LEN = int(min_len)
    if stopwords is not None:
        STOPWORDS_EXTRA = {s.strip().lower() for s in stopwords if str(s).strip()}
    if whitelist is not None:
        WHITELIST = {s.strip().lower() for s in whitelist if str(s).strip()}
    # Tokenize prefix/location into tokens consistent with filename parsing
    def _tok(s: str) -> List[str]:
        return [p for p in _SEPARATORS.split(_strip_noise(s.lower())) if p]
    PREFIX_TOKENS = _tok(prefix) if prefix else []
    LOCATION_TOKENS = _tok(location) if location else []

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
