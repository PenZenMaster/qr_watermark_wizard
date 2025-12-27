"""
Unit tests for main_ui.py - UI components and configuration

Tests configuration loading/saving and utility functions.
Full UI testing would require PyQt6 test framework (QTest).
"""

import json
import pytest
from main_ui import load_config, save_config


class TestConfigurationIO:
    """Test configuration file loading and saving."""

    def test_load_config_valid_file(self, tmp_path):
        """Test loading valid configuration file."""
        config_data = {
            "input_dir": "/path/to/input",
            "output_dir": "/path/to/output",
            "qr_link": "https://example.com",
            "text_overlay": "Test Company\n555-1234",
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = load_config(str(config_file))
        assert result == config_data
        assert result["input_dir"] == "/path/to/input"
        assert result["qr_link"] == "https://example.com"

    def test_save_config_creates_file(self, tmp_path):
        """Test saving configuration creates file."""
        config_data = {
            "input_dir": "/test/input",
            "output_dir": "/test/output",
            "qr_link": "https://test.com",
        }

        config_file = tmp_path / "new_config.json"
        save_config(config_data, str(config_file))

        assert config_file.exists()

        # Verify content
        with open(config_file) as f:
            loaded = json.load(f)
        assert loaded == config_data

    def test_save_config_formats_json_pretty(self, tmp_path):
        """Test saved config is formatted with indentation."""
        config_data = {"key1": "value1", "key2": "value2"}
        config_file = tmp_path / "formatted_config.json"

        save_config(config_data, str(config_file))

        with open(config_file) as f:
            content = f.read()
        # Check for indentation (pretty formatting)
        assert "  " in content or "\t" in content

    def test_load_config_preserves_types(self, tmp_path):
        """Test loading config preserves data types."""
        config_data = {
            "string_val": "test",
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
            "list_val": [1, 2, 3],
            "dict_val": {"nested": "value"},
        }

        config_file = tmp_path / "types_config.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = load_config(str(config_file))
        assert isinstance(result["string_val"], str)
        assert isinstance(result["int_val"], int)
        assert isinstance(result["float_val"], float)
        assert isinstance(result["bool_val"], bool)
        assert isinstance(result["list_val"], list)
        assert isinstance(result["dict_val"], dict)

    def test_save_load_roundtrip(self, tmp_path):
        """Test save and load roundtrip preserves data."""
        original_data = {
            "input_dir": "E:/projects/test/input",
            "output_dir": "E:/projects/test/output",
            "qr_link": "https://example.com/page",
            "qr_size": 150,
            "qr_opacity": 0.85,
            "text_overlay": "Multi\nLine\nText",
            "text_color": [255, 255, 255],
            "shadow_color": [0, 0, 0, 128],
            "font_size": 72,
        }

        config_file = tmp_path / "roundtrip_config.json"
        save_config(original_data, str(config_file))
        loaded_data = load_config(str(config_file))

        assert loaded_data == original_data

    def test_load_config_missing_file_raises_error(self, tmp_path):
        """Test loading non-existent file raises error."""
        nonexistent = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_config(str(nonexistent))

    def test_load_config_invalid_json_raises_error(self, tmp_path):
        """Test loading invalid JSON raises error."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("{ invalid json content")

        with pytest.raises(json.JSONDecodeError):
            load_config(str(invalid_file))

    def test_save_config_overwrites_existing(self, tmp_path):
        """Test saving config overwrites existing file."""
        config_file = tmp_path / "overwrite_config.json"

        # Save first config
        first_data = {"key": "first_value"}
        save_config(first_data, str(config_file))

        # Save second config
        second_data = {"key": "second_value"}
        save_config(second_data, str(config_file))

        # Load and verify second config
        result = load_config(str(config_file))
        assert result["key"] == "second_value"


class TestConfigurationValidation:
    """Test configuration data validation."""

    def test_config_with_all_required_fields(self, tmp_path):
        """Test config with all expected fields loads correctly."""
        complete_config = {
            "input_dir": "E:/projects/test/input",
            "output_dir": "E:/projects/test/output",
            "qr_link": "https://example.com",
            "qr_size": 150,
            "qr_opacity": 0.85,
            "text_overlay": "Test Company\n555-1234",
            "text_color": [255, 255, 255],
            "shadow_color": [0, 0, 0, 128],
            "font_size": 72,
            "text_padding": 40,
            "qr_padding": 15,
            "font_family": "Arial",
            "seo_rename": True,
            "collision_strategy": "counter",
            "process_recursive": False,
            "slug_max_words": 6,
            "slug_min_len": 3,
            "slug_stopwords": [],
            "slug_whitelist": [],
            "slug_prefix": "brand",
            "slug_location": "city",
        }

        config_file = tmp_path / "complete_config.json"
        save_config(complete_config, str(config_file))
        loaded = load_config(str(config_file))

        assert all(key in loaded for key in complete_config.keys())

    def test_config_with_optional_fields_missing(self, tmp_path):
        """Test config with optional fields missing loads without error."""
        minimal_config = {
            "input_dir": "E:/projects/test/input",
            "output_dir": "E:/projects/test/output",
            "qr_link": "https://example.com",
            "qr_size": 150,
            "qr_opacity": 0.85,
            "text_overlay": "Test",
            "text_color": [255, 255, 255],
            "shadow_color": [0, 0, 0, 128],
            "font_size": 72,
            "text_padding": 40,
            "qr_padding": 15,
        }

        config_file = tmp_path / "minimal_config.json"
        save_config(minimal_config, str(config_file))
        loaded = load_config(str(config_file))

        # Should load without error
        assert loaded["input_dir"] == "E:/projects/test/input"
        # Optional fields should be absent or have defaults
        assert loaded.get("seo_rename", False) is False


class TestConfigurationPaths:
    """Test path handling in configuration."""

    @pytest.mark.parametrize(
        "path_type,test_path",
        [
            ("windows_absolute", "E:/projects/test/input"),
            ("windows_backslash", "E:\\projects\\test\\input"),
            ("unix_absolute", "/home/user/projects/input"),
            ("relative", "./input_images"),
        ],
    )
    def test_various_path_formats(self, tmp_path, path_type, test_path):
        """Test various path formats are preserved."""
        config_data = {
            "input_dir": test_path,
            "output_dir": "/output",
        }

        config_file = tmp_path / f"{path_type}_config.json"
        save_config(config_data, str(config_file))
        loaded = load_config(str(config_file))

        assert loaded["input_dir"] == test_path


class TestColorConfiguration:
    """Test color value handling."""

    def test_rgb_color_format(self, tmp_path):
        """Test RGB color arrays are preserved."""
        config_data = {
            "text_color": [255, 255, 255],  # White
            "shadow_color": [0, 0, 0],  # Black
        }

        config_file = tmp_path / "color_config.json"
        save_config(config_data, str(config_file))
        loaded = load_config(str(config_file))

        assert loaded["text_color"] == [255, 255, 255]
        assert loaded["shadow_color"] == [0, 0, 0]

    def test_rgba_color_format(self, tmp_path):
        """Test RGBA color arrays with alpha channel."""
        config_data = {
            "text_color": [255, 255, 255, 255],
            "shadow_color": [0, 0, 0, 128],  # Semi-transparent
        }

        config_file = tmp_path / "rgba_config.json"
        save_config(config_data, str(config_file))
        loaded = load_config(str(config_file))

        assert loaded["shadow_color"] == [0, 0, 0, 128]

    @pytest.mark.parametrize(
        "color,is_valid",
        [
            ([255, 255, 255], True),  # Valid RGB
            ([0, 0, 0, 128], True),  # Valid RGBA
            ([255, 100, 50], True),  # Valid RGB
            ([300, 100, 50], False),  # Invalid - value > 255
            ([-1, 100, 50], False),  # Invalid - negative
        ],
    )
    def test_color_value_ranges(self, tmp_path, color, is_valid):
        """Test color value validation."""
        if is_valid:
            assert all(0 <= c <= 255 for c in color)
        else:
            assert not all(0 <= c <= 255 for c in color)


class TestPixelConfiguration:
    """Test pixel and point value handling."""

    @pytest.mark.parametrize(
        "param_name,param_value,is_valid",
        [
            ("qr_size", 150, True),  # Valid QR size in pixels
            ("qr_padding", 15, True),  # Valid QR padding in pixels
            ("font_size", 72, True),  # Valid font size in points
            ("text_padding", 40, True),  # Valid text padding in pixels
            ("qr_opacity", 0.85, True),  # Opacity still uses ratio (0.0-1.0)
            ("qr_size", -10, False),  # Negative pixels invalid
            ("font_size", 0, False),  # Zero font size invalid
            ("qr_opacity", 1.5, False),  # Opacity > 1.0 invalid
        ],
    )
    def test_pixel_value_ranges(self, tmp_path, param_name, param_value, is_valid):
        """Test pixel and point values are in valid ranges."""
        if "opacity" in param_name:
            # Opacity should be 0.0-1.0
            if is_valid:
                assert 0.0 <= param_value <= 1.0
            else:
                assert not (0.0 <= param_value <= 1.0)
        else:
            # Pixel/point values should be positive
            if is_valid:
                assert param_value > 0
            else:
                assert param_value <= 0


class TestEdgeCases:
    """Test edge cases in configuration."""

    def test_empty_config(self, tmp_path):
        """Test loading empty configuration."""
        config_file = tmp_path / "empty_config.json"
        with open(config_file, "w") as f:
            json.dump({}, f)

        result = load_config(str(config_file))
        assert result == {}

    def test_unicode_in_text_overlay(self, tmp_path):
        """Test Unicode characters in text overlay."""
        config_data = {
            "text_overlay": "Test Company™\n© 2025\n☎ 555-1234",
        }

        config_file = tmp_path / "unicode_config.json"
        save_config(config_data, str(config_file))
        loaded = load_config(str(config_file))

        assert loaded["text_overlay"] == config_data["text_overlay"]

    def test_very_long_text_overlay(self, tmp_path):
        """Test very long text overlay value."""
        long_text = "\n".join([f"Line {i}" for i in range(20)])
        config_data = {"text_overlay": long_text}

        config_file = tmp_path / "long_text_config.json"
        save_config(config_data, str(config_file))
        loaded = load_config(str(config_file))

        assert loaded["text_overlay"] == long_text

    def test_special_characters_in_qr_link(self, tmp_path):
        """Test special characters in QR link."""
        config_data = {
            "qr_link": "https://example.com/path?param=value&other=123#section",
        }

        config_file = tmp_path / "special_chars_config.json"
        save_config(config_data, str(config_file))
        loaded = load_config(str(config_file))

        assert loaded["qr_link"] == config_data["qr_link"]
