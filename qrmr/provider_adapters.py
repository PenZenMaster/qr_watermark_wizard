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
v2.03

Comments:
- v2.03: Phase 2 COMPLETE - Stability AI provider implementation (reliable fallback)
- v2.02: Phase 2 - Ideogram provider implementation with superior text rendering
- v2.01: Phase 2 - Fal.ai provider implementation with API integration
- v2.0.0: Initial implementation for AI integration Phase 1
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Union

import fal_client
import requests


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

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "fal-ai/flux-2-flex",
        max_retries: int = 3,
        timeout: int = 240,
    ):
        """
        Initialize Fal.ai provider.

        Args:
            api_key: Fal.ai API key. If None, uses FAL_KEY environment variable.
            model: Model endpoint to use (default: fal-ai/flux-2-flex)
            max_retries: Maximum number of retries on failure (default: 3)
            timeout: Request timeout in seconds (default: 240)
        """
        self._api_key = api_key or os.environ.get("FAL_KEY", "")
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout

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
        """
        Generate images via Fal.ai API with retry logic.

        Note: FLUX.2 [flex] doesn't support num_images parameter.
        For multiple images, we make multiple sequential API calls.

        Args:
            req: Generation request parameters

        Returns:
            GenerateResult with generated images

        Raises:
            ProviderError: If generation fails after all retries
        """
        # Check API key at generation time
        if not self._api_key:
            raise ProviderError(
                message="Fal.ai API key required. Set FAL_KEY environment variable or pass api_key parameter.",
                provider=self.name,
                details={"model": self._model},
            )

        # FLUX.2 [flex] doesn't support num_images - make multiple calls
        num_images_requested = req.num_images
        all_images: List[GeneratedImage] = []
        last_request_id: Optional[str] = None

        for img_idx in range(num_images_requested):
            print(f"[INFO] Generating image {img_idx + 1}/{num_images_requested}...")

            last_error: Optional[Exception] = None

            for attempt in range(self._max_retries):
                try:
                    # Map our request to Fal.ai format (always request 1 image)
                    fal_request = self._map_request(req)

                    # Call Fal.ai API using subscribe (blocking with queue support)
                    # Set FAL_KEY for this request
                    os.environ["FAL_KEY"] = self._api_key

                    result = fal_client.subscribe(
                        self._model,
                        arguments=fal_request,
                        with_logs=False,
                    )

                    # Parse response (returns 1 image)
                    single_result = self._parse_response(result, req)
                    all_images.extend(single_result.images)
                    last_request_id = single_result.request_id

                    print(
                        f"[SUCCESS] Generated image {img_idx + 1}/{num_images_requested}"
                    )
                    break  # Success, move to next image

                except Exception as e:
                    last_error = e

                    # Don't retry on authentication errors
                    if "auth" in str(e).lower() or "api key" in str(e).lower():
                        raise ProviderError(
                            message=f"Fal.ai authentication failed: {str(e)}",
                            provider=self.name,
                            details={"model": self._model, "error": str(e)},
                        ) from e

                    # Exponential backoff before retry
                    if attempt < self._max_retries - 1:
                        backoff_time = 2**attempt  # 1s, 2s, 4s
                        print(
                            f"[WARNING] Generation attempt {attempt + 1} failed, retrying in {backoff_time}s..."
                        )
                        time.sleep(backoff_time)
                        continue

            # If all retries exhausted for this image, fail the entire request
            if last_error is not None and len(all_images) == img_idx:
                raise ProviderError(
                    message=f"Fal.ai generation failed for image {img_idx + 1}/{num_images_requested} after {self._max_retries} attempts: {str(last_error)}",
                    provider=self.name,
                    details={
                        "model": self._model,
                        "error": str(last_error),
                        "attempts": self._max_retries,
                        "images_generated": len(all_images),
                        "images_requested": num_images_requested,
                    },
                ) from last_error

        # Return combined result
        return GenerateResult(
            images=all_images,
            request_id=last_request_id,
            raw={"num_images_generated": len(all_images)},
        )

    def _map_request(self, req: GenerateRequest) -> Dict[str, Any]:
        """Map our GenerateRequest to Fal.ai API format.

        Note: num_images is NOT included - FLUX.2 [flex] doesn't support it.
        We handle multiple images by making multiple API calls in generate().
        """
        # Map image dimensions to Fal.ai image_size format
        image_size = self._get_image_size(req.width, req.height)

        fal_params: Dict[str, Any] = {
            "prompt": req.prompt,
            "image_size": image_size,
            "enable_safety_checker": True,
            "output_format": "jpeg",
        }

        # Add optional parameters
        if req.negative_prompt:
            # Fal.ai doesn't have negative_prompt in flux-2-flex
            # Could prepend to prompt or use guidance_scale
            pass

        if req.seed is not None:
            fal_params["seed"] = req.seed

        if req.guidance is not None:
            fal_params["guidance_scale"] = req.guidance

        if req.steps is not None:
            fal_params["num_inference_steps"] = min(max(req.steps, 2), 50)

        return fal_params

    def _get_image_size(self, width: int, height: int) -> Union[str, Dict[str, int]]:
        """
        Convert width/height to Fal.ai image_size format.

        Fal.ai supports: square_hd, square, portrait_4_3, portrait_16_9,
        landscape_4_3, landscape_16_9, or custom {width, height}
        """
        aspect_ratio = width / height

        # Map to predefined sizes when possible
        if abs(aspect_ratio - 1.0) < 0.1:  # Square
            return "square_hd" if width >= 1024 else "square"
        elif width > height:
            # Landscape orientation
            if abs(aspect_ratio - 4 / 3) < 0.1:  # 4:3
                return "landscape_4_3"
            elif abs(aspect_ratio - 16 / 9) < 0.1:  # 16:9
                return "landscape_16_9"
        else:
            # Portrait orientation
            inverse_ratio = height / width
            if abs(inverse_ratio - 4 / 3) < 0.1:  # 4:3
                return "portrait_4_3"
            elif abs(inverse_ratio - 16 / 9) < 0.1:  # 16:9
                return "portrait_16_9"

        # Use custom dimensions for non-standard aspect ratios
        return {"width": width, "height": height}

    def _parse_response(
        self, result: Dict[str, Any], req: GenerateRequest
    ) -> GenerateResult:
        """Parse Fal.ai API response into our GenerateResult format."""
        images: List[GeneratedImage] = []
        download_warnings: List[str] = []

        # Extract images from response
        raw_images = result.get("images", [])
        seed = result.get("seed")

        for idx, img_data in enumerate(raw_images):
            # Download image bytes from URL
            image_url = img_data.get("url")
            if not image_url:
                warning = f"Image {idx + 1}/{len(raw_images)}: No URL in response"
                download_warnings.append(warning)
                print(f"[WARNING] {warning}")
                continue

            try:
                print(
                    f"[INFO] Downloading image {idx + 1}/{len(raw_images)} from {image_url[:60]}..."
                )
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                image_bytes = response.content

                # Determine MIME type from content_type or URL
                mime_type = img_data.get("content_type", "image/jpeg")

                images.append(
                    GeneratedImage(
                        bytes=image_bytes,
                        mime_type=mime_type,
                        seed=seed,
                        provider=self.name,
                        model=self._model,
                        warnings=[],
                        meta={
                            "width": img_data.get("width"),
                            "height": img_data.get("height"),
                            "file_size": img_data.get("file_size"),
                            "url": image_url,
                        },
                    )
                )
                print(
                    f"[SUCCESS] Downloaded image {idx + 1}/{len(raw_images)} ({len(image_bytes)} bytes)"
                )
            except requests.RequestException as e:
                # Log warning but don't fail entire request
                warning = (
                    f"Image {idx + 1}/{len(raw_images)}: Download failed - {str(e)}"
                )
                download_warnings.append(warning)
                print(f"[ERROR] {warning}")
                continue

        if not images:
            raise ProviderError(
                message="No images generated",
                provider=self.name,
                details={"response": result, "warnings": download_warnings},
            )

        # If some images failed, show warning but continue
        if download_warnings:
            print(
                f"[WARNING] Generated {len(images)}/{len(raw_images)} images (some downloads failed)"
            )
            for warning in download_warnings:
                print(f"  - {warning}")

        return GenerateResult(
            images=images,
            request_id=result.get("request_id"),
            raw=result,
        )


class IdeogramProvider:
    """Ideogram provider (superior text rendering in images)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "3.0",
        max_retries: int = 3,
        timeout: int = 240,
    ):
        """
        Initialize Ideogram provider.

        Args:
            api_key: Ideogram API key. If None, uses IDEOGRAM_KEY environment variable.
            model: Model version to use (default: "3.0")
            max_retries: Maximum number of retries on failure (default: 3)
            timeout: Request timeout in seconds (default: 240)
        """
        self._api_key = api_key or os.environ.get("IDEOGRAM_KEY", "")
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout
        self._base_url = "https://api.ideogram.ai/v1"

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
        """
        Generate images via Ideogram API with retry logic.

        Ideogram excels at rendering text in images (85-90% accuracy).
        Use exact_text parameter for text that needs to appear in the image.

        Args:
            req: Generation request parameters

        Returns:
            GenerateResult with generated images

        Raises:
            ProviderError: If generation fails after all retries
        """
        # Check API key at generation time
        if not self._api_key:
            raise ProviderError(
                message="Ideogram API key required. Set IDEOGRAM_KEY environment variable or pass api_key parameter.",
                provider=self.name,
                details={"model": self._model},
            )

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                # Map our request to Ideogram format
                ideogram_request = self._map_request(req)

                # Call Ideogram API
                endpoint = f"{self._base_url}/ideogram-v{self._model}/generate"
                headers = {
                    "Api-Key": self._api_key,
                    "Content-Type": "application/json",
                }

                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=ideogram_request,
                    timeout=self._timeout,
                )
                response.raise_for_status()

                # Parse response
                return self._parse_response(response.json(), req)

            except requests.exceptions.HTTPError as e:
                last_error = e

                # Don't retry on authentication errors (401, 403)
                if e.response is not None and e.response.status_code in (401, 403):
                    raise ProviderError(
                        message=f"Ideogram authentication failed: {str(e)}",
                        provider=self.name,
                        details={
                            "model": self._model,
                            "status_code": e.response.status_code,
                        },
                    ) from e

                # Exponential backoff before retry
                if attempt < self._max_retries - 1:
                    backoff_time = 2**attempt
                    time.sleep(backoff_time)
                    continue

            except Exception as e:
                last_error = e

                # Exponential backoff before retry
                if attempt < self._max_retries - 1:
                    backoff_time = 2**attempt
                    time.sleep(backoff_time)
                    continue

        # All retries exhausted
        raise ProviderError(
            message=f"Ideogram generation failed after {self._max_retries} attempts: {str(last_error)}",
            provider=self.name,
            details={
                "model": self._model,
                "error": str(last_error),
                "attempts": self._max_retries,
            },
        ) from last_error

    def _map_request(self, req: GenerateRequest) -> Dict[str, Any]:
        """Map our GenerateRequest to Ideogram API format."""
        ideogram_params: Dict[str, Any] = {
            "prompt": req.prompt,
            "num_images": req.num_images,
        }

        # Add exact text if specified (Ideogram's specialty)
        if req.exact_text:
            # Enhance prompt with text rendering instructions
            text_instruction = " Include the text: " + ", ".join(
                f'"{text}"' for text in req.exact_text
            )
            ideogram_params["prompt"] += text_instruction

        # Map dimensions to aspect_ratio
        aspect_ratio = self._get_aspect_ratio(req.width, req.height)
        if aspect_ratio:
            ideogram_params["aspect_ratio"] = aspect_ratio
        else:
            # Use resolution for non-standard sizes
            ideogram_params["resolution"] = f"{req.width}x{req.height}"

        # Add optional parameters
        if req.negative_prompt:
            ideogram_params["negative_prompt"] = req.negative_prompt

        if req.seed is not None:
            ideogram_params["seed"] = req.seed

        if req.style:
            # Map to Ideogram style_type
            ideogram_params["style_type"] = self._map_style(req.style)

        # Set rendering speed based on steps (lower steps = faster)
        if req.steps:
            if req.steps <= 10:
                ideogram_params["rendering_speed"] = "FLASH"
            elif req.steps <= 20:
                ideogram_params["rendering_speed"] = "TURBO"
            elif req.steps >= 40:
                ideogram_params["rendering_speed"] = "QUALITY"
            # else: DEFAULT

        # Enable magic prompt for better results
        ideogram_params["magic_prompt"] = "AUTO"

        return ideogram_params

    def _get_aspect_ratio(self, width: int, height: int) -> Optional[str]:
        """
        Convert width/height to Ideogram aspect_ratio format.

        Ideogram supports: 1x1, 16x9, 9x16, 4x3, 3x4, 5x4, 4x5, 3x2, 2x3, etc.
        """
        # Calculate GCD for simplest ratio
        from math import gcd

        divisor = gcd(width, height)
        w_ratio = width // divisor
        h_ratio = height // divisor

        # Common aspect ratios Ideogram supports
        common_ratios = {
            (1, 1): "1x1",
            (16, 9): "16x9",
            (9, 16): "9x16",
            (4, 3): "4x3",
            (3, 4): "3x4",
            (5, 4): "5x4",
            (4, 5): "4x5",
            (3, 2): "3x2",
            (2, 3): "2x3",
            (16, 10): "16x10",
            (10, 16): "10x16",
        }

        return common_ratios.get((w_ratio, h_ratio))

    def _map_style(self, style: str) -> str:
        """Map generic style to Ideogram style_type."""
        style_lower = style.lower()

        if any(word in style_lower for word in ["photo", "realistic", "real"]):
            return "REALISTIC"
        elif any(word in style_lower for word in ["design", "graphic", "logo"]):
            return "DESIGN"
        elif any(
            word in style_lower for word in ["art", "painting", "fiction", "fantasy"]
        ):
            return "FICTION"
        else:
            return "AUTO"

    def _parse_response(
        self, result: Dict[str, Any], req: GenerateRequest
    ) -> GenerateResult:
        """Parse Ideogram API response into our GenerateResult format."""
        images: List[GeneratedImage] = []
        download_warnings: List[str] = []

        # Extract images from response
        data_items = result.get("data", [])

        for idx, item in enumerate(data_items):
            # Download image bytes from URL
            image_url = item.get("url")
            if not image_url:
                warning = f"Image {idx + 1}/{len(data_items)}: No URL in response"
                download_warnings.append(warning)
                print(f"[WARNING] {warning}")
                continue

            try:
                print(
                    f"[INFO] Downloading image {idx + 1}/{len(data_items)} from {image_url[:60]}..."
                )
                response = requests.get(image_url, timeout=30)
                response.raise_for_status()
                image_bytes = response.content

                # Detect MIME type from URL or default to JPEG
                mime_type = "image/jpeg"
                if image_url.endswith(".png"):
                    mime_type = "image/png"
                elif image_url.endswith(".webp"):
                    mime_type = "image/webp"

                # Extract warnings if image safety check failed
                warnings = []
                if not item.get("is_image_safe", True):
                    warnings.append("Image flagged by safety checker")

                images.append(
                    GeneratedImage(
                        bytes=image_bytes,
                        mime_type=mime_type,
                        seed=item.get("seed"),
                        provider=self.name,
                        model=f"ideogram-{self._model}",
                        warnings=warnings,
                        meta={
                            "resolution": item.get("resolution"),
                            "upscaled_resolution": item.get("upscaled_resolution"),
                            "style_type": item.get("style_type"),
                            "prompt": item.get("prompt"),
                            "url": image_url,
                        },
                    )
                )
                print(
                    f"[SUCCESS] Downloaded image {idx + 1}/{len(data_items)} ({len(image_bytes)} bytes)"
                )
            except requests.RequestException as e:
                # Log warning but don't fail entire request
                warning = (
                    f"Image {idx + 1}/{len(data_items)}: Download failed - {str(e)}"
                )
                download_warnings.append(warning)
                print(f"[ERROR] {warning}")
                continue

        if not images:
            raise ProviderError(
                message="No images generated",
                provider=self.name,
                details={"response": result, "warnings": download_warnings},
            )

        # If some images failed, show warning but continue
        if download_warnings:
            print(
                f"[WARNING] Generated {len(images)}/{len(data_items)} images (some downloads failed)"
            )
            for warning in download_warnings:
                print(f"  - {warning}")

        return GenerateResult(
            images=images,
            request_id=result.get("request_id"),
            raw=result,
        )


class StabilityProvider:
    """Stability AI provider (reliable fallback with Stable Diffusion)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "sd3-large-turbo",
        max_retries: int = 3,
        timeout: int = 240,
    ):
        """
        Initialize Stability AI provider.

        Args:
            api_key: Stability API key. If None, uses STABILITY_API_KEY environment variable.
            model: Model to use (default: sd3-large-turbo)
                   Options: sd3, sd3-turbo, sd3-medium, sd3-large, sd3-large-turbo, ultra
            max_retries: Maximum number of retries on failure (default: 3)
            timeout: Request timeout in seconds (default: 240)
        """
        self._api_key = api_key or os.environ.get("STABILITY_API_KEY", "")
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout
        self._base_url = "https://api.stability.ai/v2beta/stable-image/generate"

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
        """
        Generate images via Stability AI API with retry logic.

        Stability AI is designed for reliability and consistent results.
        Uses Stable Diffusion models for high-quality image generation.

        Args:
            req: Generation request parameters

        Returns:
            GenerateResult with generated images

        Raises:
            ProviderError: If generation fails after all retries
        """
        # Check API key at generation time
        if not self._api_key:
            raise ProviderError(
                message="Stability API key required. Set STABILITY_API_KEY environment variable or pass api_key parameter.",
                provider=self.name,
                details={"model": self._model},
            )

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                # Map our request to Stability format
                stability_data, stability_files = self._map_request(req)

                # Call Stability AI API
                endpoint = f"{self._base_url}/{self._model}"
                headers = {
                    "Authorization": f"Bearer {self._api_key}",
                    "Accept": "image/*",
                }

                response = requests.post(
                    endpoint,
                    headers=headers,
                    files=stability_files,
                    data=stability_data,
                    timeout=self._timeout,
                )
                response.raise_for_status()

                # Parse response
                return self._parse_response(response, req)

            except requests.exceptions.HTTPError as e:
                last_error = e

                # Don't retry on authentication errors (401, 403)
                if e.response is not None and e.response.status_code in (401, 403):
                    raise ProviderError(
                        message=f"Stability authentication failed: {str(e)}",
                        provider=self.name,
                        details={
                            "model": self._model,
                            "status_code": e.response.status_code,
                        },
                    ) from e

                # Exponential backoff before retry
                if attempt < self._max_retries - 1:
                    backoff_time = 2**attempt
                    time.sleep(backoff_time)
                    continue

            except Exception as e:
                last_error = e

                # Exponential backoff before retry
                if attempt < self._max_retries - 1:
                    backoff_time = 2**attempt
                    time.sleep(backoff_time)
                    continue

        # All retries exhausted
        raise ProviderError(
            message=f"Stability generation failed after {self._max_retries} attempts: {str(last_error)}",
            provider=self.name,
            details={
                "model": self._model,
                "error": str(last_error),
                "attempts": self._max_retries,
            },
        ) from last_error

    def _map_request(
        self, req: GenerateRequest
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Map our GenerateRequest to Stability AI API format."""
        # Stability uses multipart/form-data
        stability_data: Dict[str, Any] = {
            "prompt": req.prompt,
            "output_format": "jpeg",  # Default to JPEG
        }

        # Required dummy file for multipart form
        stability_files = {"none": ""}

        # Map dimensions to aspect_ratio
        aspect_ratio = self._get_aspect_ratio(req.width, req.height)
        if aspect_ratio:
            stability_data["aspect_ratio"] = aspect_ratio

        # Add optional parameters
        if req.negative_prompt:
            stability_data["negative_prompt"] = req.negative_prompt

        if req.seed is not None:
            stability_data["seed"] = req.seed

        # Stability doesn't have direct style parameter
        # Could use style presets in prompt if needed

        return stability_data, stability_files

    def _get_aspect_ratio(self, width: int, height: int) -> Optional[str]:
        """
        Convert width/height to Stability aspect_ratio format.

        Stability supports: 21:9, 16:9, 3:2, 5:4, 1:1, 4:5, 2:3, 9:16, 9:21
        """
        from math import gcd

        divisor = gcd(width, height)
        w_ratio = width // divisor
        h_ratio = height // divisor

        # Common aspect ratios Stability supports
        common_ratios = {
            (21, 9): "21:9",
            (16, 9): "16:9",
            (3, 2): "3:2",
            (5, 4): "5:4",
            (1, 1): "1:1",
            (4, 5): "4:5",
            (2, 3): "2:3",
            (9, 16): "9:16",
            (9, 21): "9:21",
        }

        return common_ratios.get((w_ratio, h_ratio))

    def _parse_response(
        self, response: requests.Response, req: GenerateRequest
    ) -> GenerateResult:
        """Parse Stability AI API response into our GenerateResult format."""
        # Stability returns image bytes directly, not JSON with URLs
        image_bytes = response.content

        # Extract metadata from response headers
        seed = response.headers.get("seed")
        finish_reason = response.headers.get("finish_reason", "SUCCESS")

        # Convert seed to int if present
        seed_int = None
        if seed:
            try:
                seed_int = int(seed)
            except ValueError:
                pass

        # Detect MIME type from Content-Type header
        content_type = response.headers.get("Content-Type", "image/jpeg")
        mime_type = content_type.split(";")[0].strip()

        # Check for content filtering
        warnings = []
        if finish_reason and finish_reason != "SUCCESS":
            warnings.append(f"Generation finished with reason: {finish_reason}")

        if not image_bytes:
            raise ProviderError(
                message="No image data in response",
                provider=self.name,
                details={"finish_reason": finish_reason},
            )

        image = GeneratedImage(
            bytes=image_bytes,
            mime_type=mime_type,
            seed=seed_int,
            provider=self.name,
            model=self._model,
            warnings=warnings,
            meta={
                "finish_reason": finish_reason,
                "content_type": content_type,
            },
        )

        return GenerateResult(
            images=[image],  # Stability returns one image per request
            request_id=None,  # No request_id in response
            raw={
                "headers": dict(response.headers),
                "status_code": response.status_code,
            },
        )


def create_default_registry(
    provider_config: Optional[Dict[str, Any]] = None,
) -> ProviderRegistry:
    """
    Create a provider registry with all available providers.

    Args:
        provider_config: Optional provider configuration dict loaded from providers.yaml.
                        Expected format:
                        {
                            'fal': {'api_key': '...', 'model': '...'},
                            'ideogram': {'api_key': '...'},
                            'stability': {'api_key': '...'}
                        }

    Returns:
        ProviderRegistry with registered providers
    """
    registry = ProviderRegistry()
    config = provider_config or {}

    # Register Fal.ai provider
    fal_config = config.get("fal", {})
    fal_provider = FalProvider(
        api_key=fal_config.get("api_key"),
        model=fal_config.get("model", "fal-ai/flux-2-flex"),
    )
    registry.register(fal_provider)

    # Register Ideogram provider
    ideogram_config = config.get("ideogram", {})
    ideogram_provider = IdeogramProvider(
        api_key=ideogram_config.get("api_key"),
        model=ideogram_config.get("model", "3.0"),
    )
    registry.register(ideogram_provider)

    # Register Stability provider
    stability_config = config.get("stability", {})
    stability_provider = StabilityProvider(
        api_key=stability_config.get("api_key"),
        model=stability_config.get("model", "sd3-large-turbo"),
    )
    registry.register(stability_provider)

    return registry


def load_provider_credentials(
    config_path: str = "config/providers.yaml",
) -> Dict[str, Any]:
    """
    Load provider credentials from YAML configuration file.

    Args:
        config_path: Path to providers.yaml file

    Returns:
        Dictionary of provider configurations

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    from .utils import load_yaml

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Provider credentials file not found: {config_path}\n"
            "Copy config/providers.yaml.example to config/providers.yaml and add your API keys."
        )

    return load_yaml(config_path)
