"""
Module/Script Name: provider_adapters.py
Path: qrmr/provider_adapters.py

Description:
Provider adapter interface and implementations for AI image generation.

Supports multiple providers:
- Fal.ai (primary, fast, cost-effective)
- Ideogram (text-strict mode for exact text rendering)
- Stability AI (fallback for reliability)

All providers implement the ImageProvider protocol for consistent interface.

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
from typing import Any, Dict, List, Optional, Protocol


@dataclass(frozen=True)
class GenerateRequest:
    """Request parameters for image generation."""

    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 512
    num_images: int = 1
    style: Optional[str] = None
    seed: Optional[int] = None
    guidance: Optional[float] = None
    steps: Optional[int] = None
    exact_text: Optional[List[str]] = None
    timeout_seconds: int = 240
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class GeneratedImage:
    """A single generated image result."""

    bytes: bytes
    mime_type: str  # "image/png", "image/jpeg", "image/webp"
    seed: Optional[int] = None
    provider: str = ""
    model: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerateResult:
    """Complete generation result with multiple images."""

    images: List[GeneratedImage]
    request_id: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class ImageProvider(Protocol):
    """Provider contract that all image generation providers must implement."""

    @property
    def name(self) -> str:
        """Provider name (e.g., 'fal', 'ideogram', 'stability')."""
        ...

    def supports_styles(self) -> bool:
        """Whether this provider supports style parameters."""
        ...

    def supports_exact_text(self) -> bool:
        """Whether this provider supports exact text rendering."""
        ...

    def max_in_flight(self) -> int:
        """Maximum concurrent requests allowed."""
        ...

    def generate(self, req: GenerateRequest) -> GenerateResult:
        """
        Generate images based on request parameters.

        This is a blocking call. Wrap in QThread/async executor in UI.

        Args:
            req: Generation request parameters

        Returns:
            GenerateResult with generated images

        Raises:
            ProviderError: If generation fails
        """
        ...


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(
        self, message: str, provider: str, details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.provider = provider
        self.details = details or {}
        super().__init__(f"[{provider}] {message}")


class ProviderRegistry:
    """Registry for managing available image generation providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, ImageProvider] = {}

    def register(self, provider: ImageProvider) -> None:
        """Register a provider in the registry."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> ImageProvider:
        """Get a provider by name."""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not registered")
        return self._providers[name]

    def available(self) -> List[str]:
        """Get list of all available provider names."""
        return sorted(self._providers.keys())

    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name in self._providers


# Mock/Stub provider implementations for Phase 1
# These will be replaced with actual API implementations in Phase 2


class FalProvider:
    """Fal.ai provider (primary, fast, cost-effective)."""

    @property
    def name(self) -> str:
        return "fal"

    def supports_styles(self) -> bool:
        return True

    def supports_exact_text(self) -> bool:
        return False

    def max_in_flight(self) -> int:
        return 5

    def generate(self, req: GenerateRequest) -> GenerateResult:
        """Generate images via Fal.ai API."""
        # Stub implementation - will be implemented in Phase 2
        raise NotImplementedError("Fal.ai provider not yet implemented")


class IdeogramProvider:
    """Ideogram provider (text-strict mode for exact text rendering)."""

    @property
    def name(self) -> str:
        return "ideogram"

    def supports_styles(self) -> bool:
        return True

    def supports_exact_text(self) -> bool:
        return True

    def max_in_flight(self) -> int:
        return 3

    def generate(self, req: GenerateRequest) -> GenerateResult:
        """Generate images via Ideogram API."""
        # Stub implementation - will be implemented in Phase 2
        raise NotImplementedError("Ideogram provider not yet implemented")


class StabilityProvider:
    """Stability AI provider (fallback for reliability)."""

    @property
    def name(self) -> str:
        return "stability"

    def supports_styles(self) -> bool:
        return True

    def supports_exact_text(self) -> bool:
        return False

    def max_in_flight(self) -> int:
        return 10

    def generate(self, req: GenerateRequest) -> GenerateResult:
        """Generate images via Stability AI API."""
        # Stub implementation - will be implemented in Phase 2
        raise NotImplementedError("Stability AI provider not yet implemented")


def create_default_registry() -> ProviderRegistry:
    """Create a provider registry with all available providers."""
    registry = ProviderRegistry()
    registry.register(FalProvider())
    registry.register(IdeogramProvider())
    registry.register(StabilityProvider())
    return registry
