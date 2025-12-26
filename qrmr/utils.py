"""
Module/Script Name: utils.py
Path: qrmr/utils.py

Description:
Utility functions for the QR Watermark Wizard package.

Provides:
- File and path utilities
- YAML/JSON loading helpers
- Validation helpers
- String utilities

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

import json
import os
from typing import Any, Dict

import yaml


def load_yaml(path: str) -> Dict[str, Any]:
    """
    Load YAML file and return as dictionary.

    Args:
        path: Path to YAML file

    Returns:
        Dictionary with YAML contents

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], path: str) -> None:
    """
    Save dictionary as YAML file.

    Args:
        data: Dictionary to save
        path: Output file path
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_json(path: str) -> Dict[str, Any]:
    """
    Load JSON file and return as dictionary.

    Args:
        path: Path to JSON file

    Returns:
        Dictionary with JSON contents

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], path: str, indent: int = 2) -> None:
    """
    Save dictionary as JSON file.

    Args:
        data: Dictionary to save
        path: Output file path
        indent: Indentation spaces (default 2)
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def ensure_dir_exists(path: str) -> None:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path
    """
    os.makedirs(path, exist_ok=True)


def get_file_size_mb(path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        path: File path

    Returns:
        File size in MB
    """
    return os.path.getsize(path) / (1024 * 1024)


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Input text

    Returns:
        Slugified text
    """
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text
