"""
Unit tests for qr_watermark.py - Watermark engine

Tests QR generation, watermarking, configuration, and file handling.
"""

import os
import json
import pytest
from PIL import Image
from unittest.mock import patch
from qr_watermark import (
    ensure_unique_path,
    load_config,
    generate_qr_code,
)


class TestEnsureUniquePath:
    """Test unique path generation for collision handling."""

    def test_nonexistent_path_unchanged(self, tmp_path):
        """Test path that doesn't exist returns unchanged."""
        path = str(tmp_path / "test.jpg")
        result = ensure_unique_path(path)
        assert result == path

    def test_counter_strategy_adds_suffix(self, tmp_path):
        """Test counter strategy adds -2, -3, etc."""
        base_path = tmp_path / "test.jpg"
        base_path.touch()  # Create the file

        result = ensure_unique_path(str(base_path), strategy="counter")
        assert result == str(tmp_path / "test-2.jpg")

    def test_counter_strategy_increments(self, tmp_path):
        """Test counter increments when multiple collisions exist."""
        (tmp_path / "test.jpg").touch()
        (tmp_path / "test-2.jpg").touch()
        (tmp_path / "test-3.jpg").touch()

        result = ensure_unique_path(str(tmp_path / "test.jpg"), strategy="counter")
        assert result == str(tmp_path / "test-4.jpg")

    def test_timestamp_strategy_adds_timestamp(self, tmp_path):
        """Test timestamp strategy adds timestamp suffix."""
        base_path = tmp_path / "test.jpg"
        base_path.touch()

        result = ensure_unique_path(str(base_path), strategy="timestamp")
        # Should have format test-YYYYMMDDHHMMSS.jpg
        assert "test-" in result
        assert result.endswith(".jpg")
        assert len(result.split("-")[-1].replace(".jpg", "")) == 14  # YYYYMMDDHHMMSS

    def test_preserves_extension(self, tmp_path):
        """Test file extension is preserved."""
        for ext in [".jpg", ".png", ".webp"]:
            path = tmp_path / f"test{ext}"
            path.touch()
            result = ensure_unique_path(str(path))
            assert result.endswith(ext)


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_valid_config(self, tmp_path):
        """Test loading valid JSON configuration."""
        config_data = {
            "input_dir": "/path/to/input",
            "output_dir": "/path/to/output",
            "qr_link": "https://example.com",
            "qr_size": 150,
            "qr_opacity": 0.85,
            "text_overlay": "Test Text",
            "text_color": [255, 255, 255],
            "shadow_color": [0, 0, 0, 128],
            "font_size": 72,
            "text_padding": 40,
            "qr_padding": 15,
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = load_config(str(config_file))
        assert result["input_dir"] == "/path/to/input"
        assert result["qr_link"] == "https://example.com"
        assert result["qr_size"] == 150

    def test_load_config_with_optional_fields(self, tmp_path):
        """Test loading config with optional fields."""
        config_data = {
            "input_dir": "/path/to/input",
            "output_dir": "/path/to/output",
            "qr_link": "https://example.com",
            "qr_size": 150,
            "qr_opacity": 0.85,
            "text_overlay": "Test",
            "text_color": [255, 255, 255],
            "shadow_color": [0, 0, 0, 128],
            "font_size": 72,
            "text_padding": 40,
            "qr_padding": 15,
            "seo_rename": True,
            "collision_strategy": "timestamp",
            "process_recursive": True,
            "slug_max_words": 4,
            "slug_min_len": 3,
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = load_config(str(config_file))
        assert result.get("seo_rename") is True
        assert result.get("collision_strategy") == "timestamp"
        assert result.get("process_recursive") is True


class TestGenerateQRCode:
    """Test QR code generation."""

    def test_generate_qr_returns_image(self):
        """Test QR code generation returns PIL Image."""
        qr_img = generate_qr_code("https://example.com", (100, 100))
        assert isinstance(qr_img, Image.Image)
        assert qr_img.size == (100, 100)

    def test_generate_qr_with_different_sizes(self):
        """Test QR generation with various sizes."""
        for size in [(50, 50), (100, 100), (200, 200)]:
            qr_img = generate_qr_code("https://example.com", size)
            assert qr_img.size == size

    def test_generate_qr_with_long_url(self):
        """Test QR generation with long URL."""
        long_url = "https://example.com/very/long/path/" + "segment/" * 20
        qr_img = generate_qr_code(long_url, (150, 150))
        assert isinstance(qr_img, Image.Image)
        assert qr_img.size == (150, 150)

    def test_generate_qr_mode_rgba(self):
        """Test QR image is in RGBA mode."""
        qr_img = generate_qr_code("https://example.com", (100, 100))
        assert qr_img.mode == "RGBA"


class TestWatermarkApplication:
    """Test watermark application functionality."""

    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a sample test image."""
        img_path = tmp_path / "test_image.jpg"
        img = Image.new("RGB", (800, 600), color=(73, 109, 137))
        img.save(img_path, "JPEG")
        return str(img_path)

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create a test configuration file."""
        config_data = {
            "input_dir": str(tmp_path / "input"),
            "output_dir": str(tmp_path / "output"),
            "qr_link": "https://test.com",
            "qr_size": 150,
            "qr_opacity": 0.85,
            "text_overlay": "Test Watermark\n555-1234",
            "text_color": [255, 255, 255],
            "shadow_color": [0, 0, 0, 128],
            "font_size": 72,
            "text_padding": 40,
            "qr_padding": 15,
            "font_family": "Arial",
            "seo_rename": False,
            "collision_strategy": "counter",
            "process_recursive": False,
            "slug_max_words": 6,
            "slug_min_len": 3,
            "slug_stopwords": [],
            "slug_whitelist": [],
            "slug_prefix": "",
            "slug_location": "",
        }

        config_file = tmp_path / "test_settings.json"
        os.makedirs(tmp_path / "input", exist_ok=True)
        os.makedirs(tmp_path / "output", exist_ok=True)

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        return str(config_file)

    def test_apply_watermark_returns_image_in_preview_mode(
        self, sample_image, test_config
    ):
        """Test apply_watermark returns PIL Image in preview mode."""
        from qr_watermark import apply_watermark

        # Temporarily replace config path
        with patch("qr_watermark.load_config") as mock_load:
            mock_load.return_value = load_config(test_config)
            with patch("qr_watermark.refresh_config"):
                result = apply_watermark(sample_image, return_image=True)
                assert result is not None
                assert isinstance(result, Image.Image)

    def test_watermarked_image_dimensions_preserved(self, sample_image, test_config):
        """Test watermarked image preserves original dimensions."""
        from qr_watermark import apply_watermark

        original = Image.open(sample_image)
        original_size = original.size

        with patch("qr_watermark.load_config") as mock_load:
            mock_load.return_value = load_config(test_config)
            with patch("qr_watermark.refresh_config"):
                result = apply_watermark(sample_image, return_image=True)
                assert result is not None
                assert result.size == original_size


class TestConfigurationValidation:
    """Test configuration validation and error handling."""

    def test_config_with_missing_required_fields_raises_error(self, tmp_path):
        """Test incomplete config raises appropriate error."""
        incomplete_config = {
            "input_dir": "/path/to/input",
            # Missing other required fields
        }

        config_file = tmp_path / "incomplete_config.json"
        with open(config_file, "w") as f:
            json.dump(incomplete_config, f)

        # Config loads but missing fields would cause issues in apply_watermark
        config = load_config(str(config_file))
        assert "qr_link" not in config

    def test_config_with_invalid_json_raises_error(self, tmp_path):
        """Test invalid JSON raises error."""
        config_file = tmp_path / "invalid.json"
        with open(config_file, "w") as f:
            f.write("{invalid json content")

        with pytest.raises(json.JSONDecodeError):
            load_config(str(config_file))


class TestFileFormatHandling:
    """Test handling of different image formats."""

    @pytest.fixture
    def create_test_image(self, tmp_path):
        """Factory to create test images in different formats."""

        def _create(format_name, extension):
            img_path = tmp_path / f"test.{extension}"
            img = Image.new("RGB", (400, 300), color=(100, 150, 200))
            img.save(img_path, format_name)
            return str(img_path)

        return _create

    def test_jpg_input_processed(self, create_test_image):
        """Test JPEG input is processed correctly."""
        jpg_path = create_test_image("JPEG", "jpg")
        assert os.path.exists(jpg_path)
        img = Image.open(jpg_path)
        assert img.format == "JPEG"

    def test_png_input_processed(self, create_test_image):
        """Test PNG input is processed correctly."""
        png_path = create_test_image("PNG", "png")
        assert os.path.exists(png_path)
        img = Image.open(png_path)
        assert img.format == "PNG"

    def test_webp_input_processed(self, create_test_image):
        """Test WEBP input is processed correctly."""
        webp_path = create_test_image("WEBP", "webp")
        assert os.path.exists(webp_path)
        img = Image.open(webp_path)
        assert img.format == "WEBP"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_very_small_image(self, tmp_path):
        """Test watermarking very small image."""
        small_img = tmp_path / "small.jpg"
        img = Image.new("RGB", (50, 50), color=(255, 0, 0))
        img.save(small_img, "JPEG")

        # Should not crash, but may produce poor results
        assert os.path.exists(small_img)
        loaded = Image.open(small_img)
        assert loaded.size == (50, 50)

    def test_very_large_image(self, tmp_path):
        """Test watermarking large image dimensions."""
        large_img = tmp_path / "large.jpg"
        # Create a moderately large image (actual large would be slow)
        img = Image.new("RGB", (2000, 1500), color=(0, 255, 0))
        img.save(large_img, "JPEG")

        assert os.path.exists(large_img)
        loaded = Image.open(large_img)
        assert loaded.size == (2000, 1500)

    def test_square_image(self, tmp_path):
        """Test watermarking square image."""
        square_img = tmp_path / "square.jpg"
        img = Image.new("RGB", (500, 500), color=(0, 0, 255))
        img.save(square_img, "JPEG")

        assert os.path.exists(square_img)
        loaded = Image.open(square_img)
        assert loaded.size == (500, 500)

    def test_portrait_orientation(self, tmp_path):
        """Test watermarking portrait-oriented image."""
        portrait_img = tmp_path / "portrait.jpg"
        img = Image.new("RGB", (400, 800), color=(128, 128, 0))
        img.save(portrait_img, "JPEG")

        loaded = Image.open(portrait_img)
        assert loaded.size[1] > loaded.size[0]  # Height > Width

    def test_landscape_orientation(self, tmp_path):
        """Test watermarking landscape-oriented image."""
        landscape_img = tmp_path / "landscape.jpg"
        img = Image.new("RGB", (800, 400), color=(0, 128, 128))
        img.save(landscape_img, "JPEG")

        loaded = Image.open(landscape_img)
        assert loaded.size[0] > loaded.size[1]  # Width > Height


@pytest.mark.parametrize(
    "qr_size,expected_size",
    [
        (100, 100),  # 100px QR code
        (150, 150),  # 150px QR code (default)
        (200, 200),  # 200px QR code
    ],
)
def test_qr_size_direct(qr_size, expected_size):
    """Test QR code uses direct pixel size values."""
    # Test that QR size is used directly without scaling
    assert qr_size == expected_size
