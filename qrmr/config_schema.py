"""
Module/Script Name: config_schema.py
Path: qrmr/config_schema.py

Description:
Configuration schema and validation for YAML-based client profiles.

Provides dataclasses for:
- Profile metadata
- Path configuration
- Generation settings
- Provider routing
- Watermark settings
- SEO naming rules
- Upload settings

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-12-24

Last Modified Date:
2025-12-24

Version:
v2.0.0

Comments:
- v2.0.0: Initial implementation for AI integration Phase 1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProfileMetadata:
    """Profile identification and metadata."""

    name: str
    slug: str
    client_id: str
    created: str
    modified: str


@dataclass
class PathsConfig:
    """Directory paths for generation, input, output, and archival."""

    generation_output_dir: str
    input_dir: str
    output_dir: str
    archive_dir: Optional[str] = None


@dataclass
class GenerationConfig:
    """AI image generation settings."""

    mode: str = "auto"  # "auto", "manual", "disabled"
    count: int = 4
    width: int = 512
    height: int = 512
    style: str = "photoreal"
    text_strict: bool = False
    exact_text: List[str] = field(default_factory=list)
    max_attempts_per_image: int = 4
    timeout_seconds: int = 240


@dataclass
class ProvidersConfig:
    """Provider routing configuration."""

    primary: str = "fal"
    text_strict_provider: str = "ideogram"
    fallback: str = "stability"


@dataclass
class WatermarkConfig:
    """QR code and text watermark settings."""

    qr_link: str
    qr_size: int = 150  # QR code size in pixels
    qr_opacity: float = 0.85
    qr_padding: int = 15  # QR padding in pixels
    text_overlay: str = ""
    text_color: List[int] = field(default_factory=lambda: [255, 255, 255])
    shadow_color: List[int] = field(default_factory=lambda: [0, 0, 0, 128])
    font_family: str = "arial"
    font_size: int = 72  # Font size in points
    text_padding: int = 40  # Text padding in pixels


@dataclass
class SEONamingConfig:
    """SEO-friendly filename generation rules."""

    enabled: bool = True
    process_recursive: bool = False
    collision_strategy: str = "counter"
    slug_prefix: str = ""
    slug_location: str = ""
    slug_max_words: int = 6
    slug_min_len: int = 3
    slug_stopwords: List[str] = field(default_factory=list)
    slug_whitelist: List[str] = field(default_factory=list)


@dataclass
class UploadConfig:
    """S3 upload configuration."""

    enabled: bool = False
    provider: str = "aws_s3"
    bucket: str = ""
    prefix: str = ""
    acl: str = "public-read"
    cache_control: str = "public, max-age=31536000, immutable"


@dataclass
class ClientProfile:
    """Complete client profile configuration."""

    profile: ProfileMetadata
    paths: PathsConfig
    generation: GenerationConfig
    providers: ProvidersConfig
    watermark: WatermarkConfig
    seo_naming: SEONamingConfig
    upload: UploadConfig

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ClientProfile:
        """Create ClientProfile from dictionary (loaded from YAML)."""
        return cls(
            profile=ProfileMetadata(**data["profile"]),
            paths=PathsConfig(**data["paths"]),
            generation=GenerationConfig(**data.get("generation", {})),
            providers=ProvidersConfig(**data.get("providers", {})),
            watermark=WatermarkConfig(**data["watermark"]),
            seo_naming=SEONamingConfig(**data.get("seo_naming", {})),
            upload=UploadConfig(**data.get("upload", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ClientProfile to dictionary for YAML export."""
        from dataclasses import asdict

        return asdict(self)


@dataclass
class AppSettings:
    """Application-level settings (shared across all profiles)."""

    theme: str = "light"
    last_used_profile: Optional[str] = None
    recent_profiles: List[str] = field(default_factory=list)
    default_generation_dir: Optional[str] = None
    default_input_dir: Optional[str] = None
    default_output_dir: Optional[str] = None
    watch_folder_enabled: bool = False
    watch_folder_path: Optional[str] = None
    auto_process: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AppSettings:
        """Create AppSettings from dictionary (loaded from JSON)."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert AppSettings to dictionary for JSON export."""
        from dataclasses import asdict

        return asdict(self)
