"""
Module/Script Name: __init__.py
Path: qrmr/__init__.py

Description:
QR Watermark Wizard package - AI image generation, watermarking, and SEO optimization.

This package provides:
- AI image generation with multiple provider support (OpenAI, Ideogram, Stability AI)
- Provider adapter interface and registry
- YAML-based client profile management
- Configuration schema and validation
- S3 upload integration
- Pipeline orchestration

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-12-24

Last Modified Date:
2025-12-24

Version:
v2.0.0

Comments:
- v2.0.0: Initial package creation for AI integration Phase 1
"""

__version__ = "2.0.0"
__all__ = [
    "config_schema",
    "config_store",
    "image_generation",
    "provider_adapters",
    "utils",
]
