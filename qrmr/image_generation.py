"""
Module/Script Name: image_generation.py
Path: qrmr/image_generation.py

Description:
Orchestration layer for AI image generation with provider routing and retry logic.

Features:
- Smart provider routing (text-strict mode uses Ideogram, else Fal)
- Automatic retry with fallback provider on failures
- Image saving to disk with metadata
- Progress tracking and error handling
- Thread-safe design for PyQt6 integration

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
import time
from typing import Callable, List, Optional, Tuple


from .config_schema import ClientProfile
from .provider_adapters import (
    GenerateRequest,
    GenerateResult,
    ImageProvider,
    ProviderError,
    ProviderRegistry,
)


class GenerationOrchestrator:
    """Orchestrates AI image generation with provider routing and retry logic."""

    def __init__(self, registry: ProviderRegistry, profile: ClientProfile):
        """
        Initialize generation orchestrator.

        Args:
            registry: Provider registry with available providers
            profile: Client profile with generation settings
        """
        self.registry = registry
        self.profile = profile
        self.generation_config = profile.generation
        self.providers_config = profile.providers

    def _select_provider(self, text_strict: bool = False) -> Tuple[ImageProvider, str]:
        """
        Select appropriate provider based on requirements.

        Args:
            text_strict: Whether exact text rendering is required

        Returns:
            Tuple of (provider, provider_name)
        """
        if text_strict and self.generation_config.text_strict:
            provider_name = self.providers_config.text_strict_provider
        else:
            provider_name = self.providers_config.primary

        provider = self.registry.get(provider_name)
        return provider, provider_name

    def _get_fallback_provider(self) -> Tuple[Optional[ImageProvider], Optional[str]]:
        """
        Get fallback provider for retry attempts.

        Returns:
            Tuple of (provider, provider_name) or (None, None) if no fallback
        """
        fallback_name = self.providers_config.fallback
        if not self.registry.has_provider(fallback_name):
            return None, None

        provider = self.registry.get(fallback_name)
        return provider, fallback_name

    def generate_images(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> GenerateResult:
        """
        Generate images with automatic provider routing and retry logic.

        Args:
            prompt: Text prompt for image generation
            negative_prompt: Optional negative prompt
            progress_callback: Optional callback for progress updates (percent: int, message: str)

        Returns:
            GenerateResult with generated images

        Raises:
            ProviderError: If all providers fail
        """
        # Build request from profile settings
        request = GenerateRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=self.generation_config.width,
            height=self.generation_config.height,
            num_images=self.generation_config.count,
            style=self.generation_config.style,
            exact_text=(
                self.generation_config.exact_text
                if self.generation_config.text_strict
                else None
            ),
            timeout_seconds=self.generation_config.timeout_seconds,
        )

        # Select primary provider
        text_strict = bool(self.generation_config.exact_text)
        provider, provider_name = self._select_provider(text_strict)

        if progress_callback:
            progress_callback(10, f"Using {provider_name} provider")

        # Attempt generation with primary provider
        try:
            if progress_callback:
                progress_callback(20, "Generating images...")

            result = provider.generate(request)

            if progress_callback:
                progress_callback(
                    100, f"Successfully generated {len(result.images)} images"
                )

            return result

        except ProviderError as e:
            # Try fallback provider
            if progress_callback:
                progress_callback(50, "Primary provider failed, trying fallback")

            fallback_provider, fallback_name = self._get_fallback_provider()
            if not fallback_provider or not fallback_name:
                raise ProviderError(
                    "Primary provider failed and no fallback available",
                    provider_name,
                    {"original_error": str(e)},
                )

            try:
                if progress_callback:
                    progress_callback(60, f"Using {fallback_name} provider")

                result = fallback_provider.generate(request)

                if progress_callback:
                    progress_callback(
                        100, f"Successfully generated {len(result.images)} images"
                    )

                return result

            except ProviderError as fallback_error:
                raise ProviderError(
                    "Both primary and fallback providers failed",
                    fallback_name,
                    {
                        "primary_error": str(e),
                        "fallback_error": str(fallback_error),
                    },
                )

    def save_images(
        self,
        result: GenerateResult,
        output_dir: Optional[str] = None,
        prefix: str = "generated",
    ) -> List[str]:
        """
        Save generated images to disk.

        Args:
            result: Generation result with images
            output_dir: Output directory (defaults to profile's generation_output_dir)
            prefix: Filename prefix

        Returns:
            List of saved file paths
        """
        if output_dir is None:
            output_dir = self.profile.paths.generation_output_dir

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        saved_paths = []
        timestamp = int(time.time())

        for idx, image in enumerate(result.images):
            # Determine file extension from mime type
            ext_map = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/webp": ".webp",
            }
            ext = ext_map.get(image.mime_type, ".png")

            # Build filename
            filename = f"{prefix}_{timestamp}_{idx + 1}{ext}"
            filepath = os.path.join(output_dir, filename)

            # Save image bytes to file
            with open(filepath, "wb") as f:
                f.write(image.bytes)

            saved_paths.append(filepath)

        return saved_paths
