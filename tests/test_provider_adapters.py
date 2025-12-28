"""
Unit tests for qrmr/provider_adapters.py - AI image generation providers

Tests FalProvider implementation including:
- Authentication and configuration
- Request mapping
- Response parsing
- Error handling and retries
- Provider registry
"""

import os
from unittest.mock import Mock, patch

import pytest
import requests

from qrmr.provider_adapters import (
    FalProvider,
    GeneratedImage,
    GenerateRequest,
    GenerateResult,
    IdeogramProvider,
    ProviderError,
    ProviderRegistry,
    StabilityProvider,
    create_default_registry,
    load_provider_credentials,
)


class TestFalProvider:
    """Test FalProvider implementation."""

    def test_init_with_api_key(self):
        """Test FalProvider initialization with API key."""
        provider = FalProvider(api_key="test-key-123")
        assert provider.name == "fal"
        assert provider._api_key == "test-key-123"
        assert provider._model == "fal-ai/flux-2-flex"
        assert provider._max_retries == 3

    def test_init_from_environment(self):
        """Test FalProvider initialization from environment variable."""
        with patch.dict(os.environ, {"FAL_KEY": "env-key-456"}):
            provider = FalProvider()
            assert provider._api_key == "env-key-456"

    def test_init_with_custom_model(self):
        """Test FalProvider initialization with custom model."""
        provider = FalProvider(api_key="test-key", model="fal-ai/flux-pro")
        assert provider._model == "fal-ai/flux-pro"

    def test_supports_styles(self):
        """Test that FalProvider supports styles."""
        provider = FalProvider(api_key="test-key")
        assert provider.supports_styles() is True

    def test_supports_exact_text(self):
        """Test that FalProvider does not support exact text."""
        provider = FalProvider(api_key="test-key")
        assert provider.supports_exact_text() is False

    def test_max_in_flight(self):
        """Test max concurrent requests."""
        provider = FalProvider(api_key="test-key")
        assert provider.max_in_flight() == 5

    def test_generate_without_api_key(self):
        """Test that generation fails without API key."""
        provider = FalProvider()  # No API key
        request = GenerateRequest(prompt="test prompt")

        with pytest.raises(ProviderError) as exc_info:
            provider.generate(request)

        assert "API key required" in str(exc_info.value)

    @patch("qrmr.provider_adapters.fal_client")
    @patch("qrmr.provider_adapters.requests")
    def test_generate_success(self, mock_requests, mock_fal_client):
        """Test successful image generation."""
        # Mock fal_client.subscribe response
        mock_fal_client.subscribe.return_value = {
            "images": [
                {
                    "url": "https://example.com/image1.jpg",
                    "content_type": "image/jpeg",
                    "width": 1024,
                    "height": 768,
                    "file_size": 204800,
                }
            ],
            "seed": 12345,
            "request_id": "req-abc123",
        }

        # Mock requests.get for image download
        mock_response = Mock()
        mock_response.content = b"fake-image-data"
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        provider = FalProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="a cute cat",
            width=1024,
            height=768,
            num_images=1,
            seed=12345,
        )

        result = provider.generate(request)

        # Verify result
        assert isinstance(result, GenerateResult)
        assert len(result.images) == 1
        assert result.request_id == "req-abc123"

        # Verify image
        image = result.images[0]
        assert isinstance(image, GeneratedImage)
        assert image.bytes == b"fake-image-data"
        assert image.mime_type == "image/jpeg"
        assert image.seed == 12345
        assert image.provider == "fal"
        assert image.model == "fal-ai/flux-2-flex"
        assert image.meta["width"] == 1024
        assert image.meta["height"] == 768

        # Verify fal_client was called correctly
        mock_fal_client.subscribe.assert_called_once()
        call_args = mock_fal_client.subscribe.call_args
        assert call_args[0][0] == "fal-ai/flux-2-flex"
        assert "arguments" in call_args[1]
        assert call_args[1]["arguments"]["prompt"] == "a cute cat"

    @patch("qrmr.provider_adapters.fal_client")
    def test_generate_with_retry(self, mock_fal_client):
        """Test retry logic on transient failures."""
        # First call fails, second succeeds
        mock_fal_client.subscribe.side_effect = [
            Exception("Network error"),
            {
                "images": [
                    {
                        "url": "https://example.com/image1.jpg",
                        "content_type": "image/jpeg",
                    }
                ],
                "seed": 12345,
            },
        ]

        with patch("qrmr.provider_adapters.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.content = b"fake-image-data"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with patch("qrmr.provider_adapters.time.sleep"):  # Skip sleep delays
                provider = FalProvider(api_key="test-key", max_retries=3)
                request = GenerateRequest(prompt="test")

                result = provider.generate(request)

                # Should succeed after retry
                assert len(result.images) == 1
                assert mock_fal_client.subscribe.call_count == 2

    @patch("qrmr.provider_adapters.fal_client")
    def test_generate_auth_error_no_retry(self, mock_fal_client):
        """Test that authentication errors are not retried."""
        mock_fal_client.subscribe.side_effect = Exception("Invalid API key")

        provider = FalProvider(api_key="bad-key")
        request = GenerateRequest(prompt="test")

        with pytest.raises(ProviderError) as exc_info:
            provider.generate(request)

        assert "authentication failed" in str(exc_info.value).lower()
        # Should fail immediately without retries
        assert mock_fal_client.subscribe.call_count == 1

    @patch("qrmr.provider_adapters.fal_client")
    def test_generate_max_retries_exhausted(self, mock_fal_client):
        """Test failure after exhausting all retries."""
        mock_fal_client.subscribe.side_effect = Exception("Server error")

        with patch("qrmr.provider_adapters.time.sleep"):  # Skip sleep delays
            provider = FalProvider(api_key="test-key", max_retries=2)
            request = GenerateRequest(prompt="test")

            with pytest.raises(ProviderError) as exc_info:
                provider.generate(request)

            assert "after 2 attempts" in str(exc_info.value)
            assert mock_fal_client.subscribe.call_count == 2

    def test_map_request_basic(self):
        """Test basic request parameter mapping.

        Note: num_images is NOT in the mapped request because FLUX.2 [flex]
        doesn't support it. Multiple images are handled in generate() method.
        """
        provider = FalProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="test prompt",
            width=1024,
            height=1024,
            num_images=2,
        )

        fal_request = provider._map_request(request)

        assert fal_request["prompt"] == "test prompt"
        assert "num_images" not in fal_request  # FLUX.2 doesn't support this
        assert fal_request["image_size"] == "square_hd"
        assert fal_request["enable_safety_checker"] is True
        assert fal_request["output_format"] == "jpeg"

    def test_map_request_with_optional_params(self):
        """Test request mapping with optional parameters."""
        provider = FalProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="test",
            seed=42,
            guidance=7.5,
            steps=30,
            width=512,
            height=512,
        )

        fal_request = provider._map_request(request)

        assert fal_request["seed"] == 42
        assert fal_request["guidance_scale"] == 7.5
        assert fal_request["num_inference_steps"] == 30

    def test_map_request_steps_clamping(self):
        """Test that inference steps are clamped to valid range."""
        provider = FalProvider(api_key="test-key")

        # Test too low
        request = GenerateRequest(prompt="test", steps=1)
        fal_request = provider._map_request(request)
        assert fal_request["num_inference_steps"] == 2

        # Test too high
        request = GenerateRequest(prompt="test", steps=100)
        fal_request = provider._map_request(request)
        assert fal_request["num_inference_steps"] == 50

    def test_get_image_size_square(self):
        """Test image size mapping for square aspect ratios."""
        provider = FalProvider(api_key="test-key")

        # Square HD
        assert provider._get_image_size(1024, 1024) == "square_hd"

        # Square
        assert provider._get_image_size(512, 512) == "square"

    def test_get_image_size_4_3(self):
        """Test image size mapping for 4:3 aspect ratio."""
        provider = FalProvider(api_key="test-key")

        # Landscape 4:3
        assert provider._get_image_size(1024, 768) == "landscape_4_3"

        # Portrait 4:3
        assert provider._get_image_size(768, 1024) == "portrait_4_3"

    def test_get_image_size_16_9(self):
        """Test image size mapping for 16:9 aspect ratio."""
        provider = FalProvider(api_key="test-key")

        # Landscape 16:9
        assert provider._get_image_size(1920, 1080) == "landscape_16_9"

        # Portrait 16:9
        assert provider._get_image_size(1080, 1920) == "portrait_16_9"

    def test_get_image_size_custom(self):
        """Test custom image size for non-standard aspect ratios."""
        provider = FalProvider(api_key="test-key")

        # Custom aspect ratio
        result = provider._get_image_size(1200, 800)
        assert isinstance(result, dict)
        assert result["width"] == 1200
        assert result["height"] == 800

    @patch("qrmr.provider_adapters.requests.get")
    def test_parse_response_success(self, mock_get):
        """Test successful response parsing."""
        mock_response = Mock()
        mock_response.content = b"image-data-123"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        provider = FalProvider(api_key="test-key")
        fal_response = {
            "images": [
                {
                    "url": "https://example.com/img1.jpg",
                    "content_type": "image/jpeg",
                    "width": 1024,
                    "height": 768,
                }
            ],
            "seed": 99999,
            "request_id": "req-xyz",
        }

        request = GenerateRequest(prompt="test")
        result = provider._parse_response(fal_response, request)

        assert len(result.images) == 1
        assert result.request_id == "req-xyz"
        assert result.images[0].bytes == b"image-data-123"
        assert result.images[0].seed == 99999

    @patch("qrmr.provider_adapters.requests.get")
    def test_parse_response_no_images(self, mock_get):
        """Test error when no images in response."""
        provider = FalProvider(api_key="test-key")
        fal_response = {"images": [], "seed": 123}

        request = GenerateRequest(prompt="test")

        with pytest.raises(ProviderError) as exc_info:
            provider._parse_response(fal_response, request)

        assert "No images generated" in str(exc_info.value)

    @patch("qrmr.provider_adapters.requests.get")
    def test_parse_response_download_failure(self, mock_get):
        """Test handling of image download failures."""
        # First image download fails, should continue
        mock_get.side_effect = requests.RequestException("Download failed")

        provider = FalProvider(api_key="test-key")
        fal_response = {
            "images": [
                {"url": "https://example.com/img1.jpg"},
                {"url": "https://example.com/img2.jpg"},
            ],
            "seed": 123,
        }

        request = GenerateRequest(prompt="test")

        # Should raise error because all downloads failed
        with pytest.raises(ProviderError):
            provider._parse_response(fal_response, request)


class TestProviderRegistry:
    """Test ProviderRegistry functionality."""

    def test_register_provider(self):
        """Test registering a provider."""
        registry = ProviderRegistry()
        provider = FalProvider(api_key="test-key")

        registry.register(provider)

        assert registry.has_provider("fal")
        assert registry.get("fal") == provider

    def test_get_nonexistent_provider(self):
        """Test getting a provider that doesn't exist."""
        registry = ProviderRegistry()

        with pytest.raises(KeyError) as exc_info:
            registry.get("nonexistent")

        assert "not registered" in str(exc_info.value)

    def test_available_providers(self):
        """Test listing available providers."""
        registry = ProviderRegistry()
        registry.register(FalProvider(api_key="test-key"))

        available = registry.available()
        assert "fal" in available
        assert isinstance(available, list)


class TestIdeogramProvider:
    """Test IdeogramProvider implementation."""

    def test_init_with_api_key(self):
        """Test IdeogramProvider initialization with API key."""
        provider = IdeogramProvider(api_key="test-key-123")
        assert provider.name == "ideogram"
        assert provider._api_key == "test-key-123"
        assert provider._model == "3.0"
        assert provider._max_retries == 3

    def test_init_from_environment(self):
        """Test IdeogramProvider initialization from environment variable."""
        with patch.dict(os.environ, {"IDEOGRAM_KEY": "env-key-456"}):
            provider = IdeogramProvider()
            assert provider._api_key == "env-key-456"

    def test_init_with_custom_model(self):
        """Test IdeogramProvider initialization with custom model."""
        provider = IdeogramProvider(api_key="test-key", model="2.0")
        assert provider._model == "2.0"

    def test_supports_styles(self):
        """Test that IdeogramProvider supports styles."""
        provider = IdeogramProvider(api_key="test-key")
        assert provider.supports_styles() is True

    def test_supports_exact_text(self):
        """Test that IdeogramProvider supports exact text rendering."""
        provider = IdeogramProvider(api_key="test-key")
        assert provider.supports_exact_text() is True

    def test_max_in_flight(self):
        """Test max concurrent requests."""
        provider = IdeogramProvider(api_key="test-key")
        assert provider.max_in_flight() == 3

    def test_generate_without_api_key(self):
        """Test that generation fails without API key."""
        provider = IdeogramProvider()  # No API key
        request = GenerateRequest(prompt="test prompt")

        with pytest.raises(ProviderError) as exc_info:
            provider.generate(request)

        assert "API key required" in str(exc_info.value)

    @patch("qrmr.provider_adapters.requests")
    def test_generate_success(self, mock_requests):
        """Test successful image generation."""
        # Mock API response
        mock_api_response = Mock()
        mock_api_response.json.return_value = {
            "data": [
                {
                    "url": "https://example.com/image1.jpg",
                    "prompt": "A picture of a cat",
                    "resolution": "1024x768",
                    "seed": 12345,
                    "is_image_safe": True,
                    "style_type": "GENERAL",
                }
            ],
            "created": "2025-12-26T00:00:00Z",
        }
        mock_api_response.raise_for_status = Mock()

        # Mock image download
        mock_image_response = Mock()
        mock_image_response.content = b"fake-image-data"
        mock_image_response.raise_for_status = Mock()

        mock_requests.post.return_value = mock_api_response
        mock_requests.get.return_value = mock_image_response

        provider = IdeogramProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="a cute cat",
            width=1024,
            height=768,
            num_images=1,
            seed=12345,
        )

        result = provider.generate(request)

        # Verify result
        assert isinstance(result, GenerateResult)
        assert len(result.images) == 1

        # Verify image
        image = result.images[0]
        assert isinstance(image, GeneratedImage)
        assert image.bytes == b"fake-image-data"
        assert image.seed == 12345
        assert image.provider == "ideogram"
        assert image.model == "ideogram-3.0"
        assert image.meta["resolution"] == "1024x768"
        assert image.warnings == []

        # Verify API call
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "https://api.ideogram.ai/v1/ideogram-v3.0/generate" in call_args[0][0]
        assert call_args[1]["headers"]["Api-Key"] == "test-key"
        assert call_args[1]["json"]["prompt"] == "a cute cat"

    @patch("qrmr.provider_adapters.requests")
    def test_generate_with_exact_text(self, mock_requests):
        """Test generation with exact text rendering."""
        mock_api_response = Mock()
        mock_api_response.json.return_value = {
            "data": [
                {
                    "url": "https://example.com/image1.jpg",
                    "seed": 123,
                    "is_image_safe": True,
                }
            ]
        }
        mock_api_response.raise_for_status = Mock()

        mock_image_response = Mock()
        mock_image_response.content = b"fake-image-data"
        mock_image_response.raise_for_status = Mock()

        mock_requests.post.return_value = mock_api_response
        mock_requests.get.return_value = mock_image_response

        provider = IdeogramProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="a business card",
            exact_text=["John Doe", "CEO", "555-1234"],
        )

        provider.generate(request)

        # Verify exact text was added to prompt
        call_json = mock_requests.post.call_args[1]["json"]
        assert 'Include the text: "John Doe", "CEO", "555-1234"' in call_json["prompt"]

    @patch("qrmr.provider_adapters.requests.post")
    def test_generate_auth_error(self, mock_post):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = requests.exceptions.HTTPError(response=mock_response)
        mock_post.side_effect = mock_error

        provider = IdeogramProvider(api_key="bad-key")
        request = GenerateRequest(prompt="test")

        with pytest.raises(ProviderError) as exc_info:
            provider.generate(request)

        assert "authentication failed" in str(exc_info.value).lower()
        # Should not retry auth errors
        assert mock_post.call_count == 1

    @patch("qrmr.provider_adapters.requests.get")
    @patch("qrmr.provider_adapters.requests.post")
    def test_generate_with_retry(self, mock_post, mock_get):
        """Test retry logic on transient failures."""
        # First call fails, second succeeds
        mock_success = Mock()
        mock_success.json.return_value = {
            "data": [
                {
                    "url": "https://example.com/img.jpg",
                    "seed": 123,
                    "is_image_safe": True,
                }
            ]
        }
        mock_success.raise_for_status = Mock()

        mock_image = Mock()
        mock_image.content = b"data"
        mock_image.raise_for_status = Mock()

        mock_post.side_effect = [
            requests.exceptions.RequestException("Network error"),
            mock_success,
        ]
        mock_get.return_value = mock_image

        with patch("qrmr.provider_adapters.time.sleep"):  # Skip delays
            provider = IdeogramProvider(api_key="test-key", max_retries=3)
            request = GenerateRequest(prompt="test")

            result = provider.generate(request)
            assert len(result.images) == 1
            assert mock_post.call_count == 2

    def test_map_request_basic(self):
        """Test basic request parameter mapping."""
        provider = IdeogramProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="test prompt",
            width=1024,
            height=768,
            num_images=2,
        )

        ideogram_request = provider._map_request(request)

        assert ideogram_request["prompt"] == "test prompt"
        assert ideogram_request["num_images"] == 2
        assert ideogram_request["aspect_ratio"] == "4x3"
        assert ideogram_request["magic_prompt"] == "AUTO"

    def test_map_request_with_style(self):
        """Test request mapping with style."""
        provider = IdeogramProvider(api_key="test-key")

        # Realistic style
        request = GenerateRequest(prompt="test", style="photorealistic")
        result = provider._map_request(request)
        assert result["style_type"] == "REALISTIC"

        # Design style
        request = GenerateRequest(prompt="test", style="graphic design")
        result = provider._map_request(request)
        assert result["style_type"] == "DESIGN"

        # Fiction style
        request = GenerateRequest(prompt="test", style="fantasy art")
        result = provider._map_request(request)
        assert result["style_type"] == "FICTION"

    def test_map_request_rendering_speed(self):
        """Test rendering speed mapping from steps."""
        provider = IdeogramProvider(api_key="test-key")

        # FLASH (steps <= 10)
        request = GenerateRequest(prompt="test", steps=5)
        result = provider._map_request(request)
        assert result["rendering_speed"] == "FLASH"

        # TURBO (steps <= 20)
        request = GenerateRequest(prompt="test", steps=15)
        result = provider._map_request(request)
        assert result["rendering_speed"] == "TURBO"

        # QUALITY (steps >= 40)
        request = GenerateRequest(prompt="test", steps=50)
        result = provider._map_request(request)
        assert result["rendering_speed"] == "QUALITY"

    def test_get_aspect_ratio_common(self):
        """Test aspect ratio calculation for common ratios."""
        provider = IdeogramProvider(api_key="test-key")

        assert provider._get_aspect_ratio(1024, 1024) == "1x1"
        assert provider._get_aspect_ratio(1920, 1080) == "16x9"
        assert provider._get_aspect_ratio(1080, 1920) == "9x16"
        assert provider._get_aspect_ratio(1024, 768) == "4x3"
        assert provider._get_aspect_ratio(768, 1024) == "3x4"

    def test_get_aspect_ratio_custom(self):
        """Test aspect ratio returns None for non-standard ratios."""
        provider = IdeogramProvider(api_key="test-key")

        # Non-standard ratio (7:5 not in common_ratios)
        result = provider._get_aspect_ratio(1400, 1000)
        assert result is None

    @patch("qrmr.provider_adapters.requests")
    def test_parse_response_with_safety_warning(self, mock_requests):
        """Test response parsing with safety check warning."""
        mock_image = Mock()
        mock_image.content = b"image-data"
        mock_image.raise_for_status = Mock()
        mock_requests.get.return_value = mock_image

        provider = IdeogramProvider(api_key="test-key")
        response_data = {
            "data": [
                {
                    "url": "https://example.com/img1.jpg",
                    "seed": 99999,
                    "is_image_safe": False,  # Safety check failed
                }
            ]
        }

        request = GenerateRequest(prompt="test")
        result = provider._parse_response(response_data, request)

        assert len(result.images) == 1
        assert "Image flagged by safety checker" in result.images[0].warnings


class TestStabilityProvider:
    """Test StabilityProvider implementation."""

    def test_init_with_api_key(self):
        """Test StabilityProvider initialization with API key."""
        provider = StabilityProvider(api_key="test-key-123")
        assert provider.name == "stability"
        assert provider._api_key == "test-key-123"
        assert provider._model == "sd3-large-turbo"
        assert provider._max_retries == 3

    def test_init_from_environment(self):
        """Test StabilityProvider initialization from environment variable."""
        with patch.dict(os.environ, {"STABILITY_API_KEY": "env-key-456"}):
            provider = StabilityProvider()
            assert provider._api_key == "env-key-456"

    def test_init_with_custom_model(self):
        """Test StabilityProvider initialization with custom model."""
        provider = StabilityProvider(api_key="test-key", model="ultra")
        assert provider._model == "ultra"

    def test_supports_styles(self):
        """Test that StabilityProvider supports styles."""
        provider = StabilityProvider(api_key="test-key")
        assert provider.supports_styles() is True

    def test_supports_exact_text(self):
        """Test that StabilityProvider does not support exact text."""
        provider = StabilityProvider(api_key="test-key")
        assert provider.supports_exact_text() is False

    def test_max_in_flight(self):
        """Test max concurrent requests."""
        provider = StabilityProvider(api_key="test-key")
        assert provider.max_in_flight() == 10

    def test_generate_without_api_key(self):
        """Test that generation fails without API key."""
        provider = StabilityProvider()  # No API key
        request = GenerateRequest(prompt="test prompt")

        with pytest.raises(ProviderError) as exc_info:
            provider.generate(request)

        assert "API key required" in str(exc_info.value)

    @patch("qrmr.provider_adapters.requests.post")
    def test_generate_success(self, mock_post):
        """Test successful image generation."""
        # Mock API response (Stability returns bytes directly)
        mock_response = Mock()
        mock_response.content = b"fake-image-data"
        mock_response.headers = {
            "seed": "12345",
            "finish_reason": "SUCCESS",
            "Content-Type": "image/jpeg",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        provider = StabilityProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="a cute cat",
            width=1024,
            height=1024,
            num_images=1,
            seed=12345,
        )

        result = provider.generate(request)

        # Verify result
        assert isinstance(result, GenerateResult)
        assert len(result.images) == 1

        # Verify image
        image = result.images[0]
        assert isinstance(image, GeneratedImage)
        assert image.bytes == b"fake-image-data"
        assert image.seed == 12345
        assert image.provider == "stability"
        assert image.model == "sd3-large-turbo"
        assert image.mime_type == "image/jpeg"
        assert image.warnings == []

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert (
            "https://api.stability.ai/v2beta/stable-image/generate/sd3-large-turbo"
            in call_args[0][0]
        )
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"
        assert call_args[1]["data"]["prompt"] == "a cute cat"

    @patch("qrmr.provider_adapters.requests.post")
    def test_generate_with_finish_reason_warning(self, mock_post):
        """Test generation with non-SUCCESS finish_reason."""
        mock_response = Mock()
        mock_response.content = b"fake-image-data"
        mock_response.headers = {
            "seed": "123",
            "finish_reason": "CONTENT_FILTERED",
            "Content-Type": "image/jpeg",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        provider = StabilityProvider(api_key="test-key")
        request = GenerateRequest(prompt="test")

        result = provider.generate(request)

        # Should have warning
        assert len(result.images) == 1
        assert "CONTENT_FILTERED" in result.images[0].warnings[0]

    @patch("qrmr.provider_adapters.requests.post")
    def test_generate_auth_error(self, mock_post):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_error = requests.exceptions.HTTPError(response=mock_response)
        mock_post.side_effect = mock_error

        provider = StabilityProvider(api_key="bad-key")
        request = GenerateRequest(prompt="test")

        with pytest.raises(ProviderError) as exc_info:
            provider.generate(request)

        assert "authentication failed" in str(exc_info.value).lower()
        # Should not retry auth errors
        assert mock_post.call_count == 1

    @patch("qrmr.provider_adapters.requests.post")
    def test_generate_with_retry(self, mock_post):
        """Test retry logic on transient failures."""
        # First call fails, second succeeds
        mock_success = Mock()
        mock_success.content = b"image-data"
        mock_success.headers = {
            "seed": "123",
            "finish_reason": "SUCCESS",
            "Content-Type": "image/jpeg",
        }
        mock_success.raise_for_status = Mock()

        mock_post.side_effect = [
            requests.exceptions.RequestException("Network error"),
            mock_success,
        ]

        with patch("qrmr.provider_adapters.time.sleep"):  # Skip delays
            provider = StabilityProvider(api_key="test-key", max_retries=3)
            request = GenerateRequest(prompt="test")

            result = provider.generate(request)
            assert len(result.images) == 1
            assert mock_post.call_count == 2

    def test_map_request_basic(self):
        """Test basic request parameter mapping."""
        provider = StabilityProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="test prompt",
            width=1024,
            height=1024,
        )

        stability_data, stability_files = provider._map_request(request)

        assert stability_data["prompt"] == "test prompt"
        assert stability_data["output_format"] == "jpeg"
        assert stability_data["aspect_ratio"] == "1:1"
        assert stability_files == {"none": ""}

    def test_map_request_with_optional_params(self):
        """Test request mapping with optional parameters."""
        provider = StabilityProvider(api_key="test-key")
        request = GenerateRequest(
            prompt="test",
            negative_prompt="bad things",
            seed=42,
            width=1920,
            height=1080,
        )

        stability_data, _ = provider._map_request(request)

        assert stability_data["negative_prompt"] == "bad things"
        assert stability_data["seed"] == 42
        assert stability_data["aspect_ratio"] == "16:9"

    def test_get_aspect_ratio_common(self):
        """Test aspect ratio calculation for common ratios."""
        provider = StabilityProvider(api_key="test-key")

        assert provider._get_aspect_ratio(1024, 1024) == "1:1"
        assert provider._get_aspect_ratio(1920, 1080) == "16:9"
        assert provider._get_aspect_ratio(1080, 1920) == "9:16"
        assert provider._get_aspect_ratio(1500, 1000) == "3:2"
        assert provider._get_aspect_ratio(1000, 1500) == "2:3"
        assert provider._get_aspect_ratio(1250, 1000) == "5:4"
        assert provider._get_aspect_ratio(1000, 1250) == "4:5"

    def test_get_aspect_ratio_custom(self):
        """Test aspect ratio returns None for non-standard ratios."""
        provider = StabilityProvider(api_key="test-key")

        # Non-standard ratio (7:5 not in common_ratios)
        result = provider._get_aspect_ratio(1400, 1000)
        assert result is None

    @patch("qrmr.provider_adapters.requests.post")
    def test_parse_response_no_image_data(self, mock_post):
        """Test error when no image data in response."""
        mock_response = Mock()
        mock_response.content = b""  # Empty
        mock_response.headers = {"finish_reason": "ERROR"}

        provider = StabilityProvider(api_key="test-key")
        request = GenerateRequest(prompt="test")

        with pytest.raises(ProviderError) as exc_info:
            provider._parse_response(mock_response, request)

        assert "No image data" in str(exc_info.value)


class TestCreateDefaultRegistry:
    """Test create_default_registry function."""

    def test_create_without_config(self):
        """Test creating registry without configuration."""
        registry = create_default_registry()

        assert registry.has_provider("fal")
        assert registry.has_provider("ideogram")
        assert registry.has_provider("stability")

    def test_create_with_config(self):
        """Test creating registry with provider configuration."""
        config = {
            "fal": {
                "api_key": "test-fal-key",
                "model": "fal-ai/flux-pro",
            }
        }

        registry = create_default_registry(provider_config=config)

        fal_provider = registry.get("fal")
        assert fal_provider._api_key == "test-fal-key"
        assert fal_provider._model == "fal-ai/flux-pro"


class TestLoadProviderCredentials:
    """Test load_provider_credentials function."""

    def test_load_missing_file(self):
        """Test error when credentials file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_provider_credentials("nonexistent.yaml")

        assert "not found" in str(exc_info.value)
        assert "providers.yaml.example" in str(exc_info.value)

    @patch("qrmr.provider_adapters.os.path.exists")
    @patch("qrmr.utils.load_yaml")
    def test_load_success(self, mock_load_yaml, mock_exists):
        """Test successful credentials loading."""
        mock_exists.return_value = True
        mock_load_yaml.return_value = {
            "fal": {"api_key": "test-key"},
            "ideogram": {"api_key": "test-key-2"},
        }

        result = load_provider_credentials("config/providers.yaml")

        assert result["fal"]["api_key"] == "test-key"
        assert result["ideogram"]["api_key"] == "test-key-2"
        mock_load_yaml.assert_called_once_with("config/providers.yaml")
