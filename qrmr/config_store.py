"""
Module/Script Name: config_store.py
Path: qrmr/config_store.py

Description:
Profile store and management for client configurations.

Provides:
- Profile loading/saving (YAML)
- Profile discovery in profiles directory
- Recent profiles management
- App settings management (JSON)
- Profile validation

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

import os
from typing import List

from .config_schema import AppSettings, ClientProfile
from .utils import load_json, load_yaml, save_json, save_yaml


class ConfigStore:
    """Manages client profiles and application settings."""

    def __init__(self, base_dir: str = "config"):
        """
        Initialize config store.

        Args:
            base_dir: Base configuration directory (default: "config")
        """
        self.base_dir = base_dir
        self.profiles_dir = os.path.join(base_dir, "profiles")
        self.app_settings_path = os.path.join(base_dir, "app_settings.json")

        # Ensure directories exist
        os.makedirs(self.profiles_dir, exist_ok=True)

    def load_profile(self, profile_slug: str) -> ClientProfile:
        """
        Load a client profile by slug.

        Args:
            profile_slug: Profile slug (e.g., "salvo-metal-works")

        Returns:
            ClientProfile instance

        Raises:
            FileNotFoundError: If profile doesn't exist
            ValueError: If profile is invalid
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_slug}.yaml")
        data = load_yaml(profile_path)
        return ClientProfile.from_dict(data)

    def save_profile(self, profile: ClientProfile) -> None:
        """
        Save a client profile.

        Args:
            profile: ClientProfile to save
        """
        profile_slug = profile.profile.slug
        profile_path = os.path.join(self.profiles_dir, f"{profile_slug}.yaml")
        data = profile.to_dict()
        save_yaml(data, profile_path)

    def list_profiles(self) -> List[str]:
        """
        List all available profile slugs.

        Returns:
            List of profile slugs
        """
        if not os.path.exists(self.profiles_dir):
            return []

        profiles = []
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(".yaml"):
                slug = filename[:-5]  # Remove .yaml extension
                profiles.append(slug)

        return sorted(profiles)

    def profile_exists(self, profile_slug: str) -> bool:
        """
        Check if a profile exists.

        Args:
            profile_slug: Profile slug

        Returns:
            True if profile exists
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_slug}.yaml")
        return os.path.exists(profile_path)

    def delete_profile(self, profile_slug: str) -> None:
        """
        Delete a profile.

        Args:
            profile_slug: Profile slug to delete
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_slug}.yaml")
        if os.path.exists(profile_path):
            os.remove(profile_path)

    def load_app_settings(self) -> AppSettings:
        """
        Load application settings.

        Returns:
            AppSettings instance (defaults if file doesn't exist)
        """
        if not os.path.exists(self.app_settings_path):
            return AppSettings()

        data = load_json(self.app_settings_path)
        return AppSettings.from_dict(data)

    def save_app_settings(self, settings: AppSettings) -> None:
        """
        Save application settings.

        Args:
            settings: AppSettings to save
        """
        data = settings.to_dict()
        save_json(data, self.app_settings_path)

    def update_recent_profiles(self, profile_slug: str, max_recent: int = 10) -> None:
        """
        Update recent profiles list.

        Args:
            profile_slug: Profile slug to add to recents
            max_recent: Maximum number of recent profiles to keep
        """
        settings = self.load_app_settings()

        # Remove if already in list
        if profile_slug in settings.recent_profiles:
            settings.recent_profiles.remove(profile_slug)

        # Add to front of list
        settings.recent_profiles.insert(0, profile_slug)

        # Trim to max_recent
        settings.recent_profiles = settings.recent_profiles[:max_recent]

        # Update last used
        settings.last_used_profile = profile_slug

        self.save_app_settings(settings)

    def get_recent_profiles(self) -> List[str]:
        """
        Get list of recent profile slugs.

        Returns:
            List of recent profile slugs
        """
        settings = self.load_app_settings()
        return settings.recent_profiles
