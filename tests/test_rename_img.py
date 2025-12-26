"""
Unit tests for rename_img.py - SEO slug generator

Tests slug generation, noise stripping, configuration, and edge cases.
"""

import pytest
from rename_img import (
    seo_friendly_name,
    configure_slug,
    _strip_noise,
    _tokenize,
    _is_meaningful,
    _dedupe,
    _slugify,
    _slug_tokens_from_name,
)


@pytest.fixture(autouse=True)
def reset_slug_config():
    """Reset slug configuration to defaults before each test."""
    configure_slug(
        max_words=6,
        min_len=3,
        stopwords=[],
        whitelist=[],
        prefix="",
        location="",
    )
    yield
    # Cleanup after test
    configure_slug(
        max_words=6,
        min_len=3,
        stopwords=[],
        whitelist=[],
        prefix="",
        location="",
    )


class TestSlugGeneration:
    """Test basic slug generation functionality."""

    def test_simple_filename(self):
        """Test basic filename without noise."""
        result = seo_friendly_name("copper-dormer-installation")
        assert result == "copper-dormer-installation.jpg"

    def test_filename_with_spaces(self):
        """Test filename with spaces converts to hyphens."""
        result = seo_friendly_name("copper dormer installation")
        assert result == "copper-dormer-installation.jpg"

    def test_filename_with_mixed_separators(self):
        """Test filename with various separators."""
        result = seo_friendly_name("copper_dormer.installation-final")
        assert "copper" in result
        assert "dormer" in result
        assert result.endswith(".jpg")

    def test_empty_filename_returns_default(self):
        """Test empty filename returns 'image.jpg'."""
        result = seo_friendly_name("")
        assert result == "image.jpg"

    def test_all_noise_returns_default(self):
        """Test filename with only noise returns default."""
        result = seo_friendly_name("IMG_20250816_DSC_FINAL")
        assert result == "image.jpg"


class TestNoiseStripping:
    """Test noise pattern removal."""

    def test_strip_dimensions(self):
        """Test dimension patterns are stripped."""
        result = _strip_noise("image-1200x800-final")
        assert "1200x800" not in result

    def test_strip_date_formats(self):
        """Test various date formats are stripped."""
        assert "2025-08-16" not in _strip_noise("photo-2025-08-16")
        assert "20250816" not in _strip_noise("photo-20250816")
        assert "08-16-2025" not in _strip_noise("photo-08-16-2025")

    def test_strip_uuid(self):
        """Test UUID patterns are stripped."""
        uuid_str = "image-550e8400-e29b-41d4-a716-446655440000"
        result = _strip_noise(uuid_str)
        assert "550e8400" not in result

    def test_strip_uuid_fragments(self):
        """Test UUID fragment patterns are stripped."""
        result = _strip_noise("photo-2c8d-c4a04fee26cb")
        assert "2c8d" not in result
        assert "c4a04fee26cb" not in result

    def test_strip_long_hex(self):
        """Test long hex strings are stripped."""
        result = _strip_noise("image-c4a04fee26cb")
        assert "c4a04fee26cb" not in result

    def test_strip_bracketed_notes(self):
        """Test bracketed content is stripped."""
        result = _strip_noise("photo(edited)final")
        assert "edited" not in result


class TestTokenization:
    """Test tokenization logic."""

    def test_tokenize_simple(self):
        """Test basic tokenization."""
        tokens = _tokenize("copper-dormer-installation")
        assert tokens == ["copper", "dormer", "installation"]

    def test_tokenize_with_noise(self):
        """Test tokenization strips noise first."""
        tokens = _tokenize("IMG_20250816_copper_dormer")
        assert "copper" in tokens
        assert "dormer" in tokens
        # Date token may appear in tokenization, but will be filtered later by _is_meaningful

    def test_tokenize_preserves_hyphens_in_multipart_names(self):
        """Test that multipart location names like 'ann-arbor' are preserved."""
        # The tokenizer splits on hyphens, but configure_slug can accept "ann-arbor" as location
        configure_slug(location="ann-arbor")
        result = seo_friendly_name("copper-dormer")
        assert "ann" in result and "arbor" in result

    def test_tokenize_empty_string(self):
        """Test tokenizing empty string."""
        tokens = _tokenize("")
        assert tokens == []


class TestMeaningfulnessFilter:
    """Test token meaningfulness filtering."""

    def test_short_tokens_filtered(self):
        """Test tokens below minimum length are filtered."""
        configure_slug(min_len=4)
        assert not _is_meaningful("hi", 4)
        assert _is_meaningful("hello", 4)

    def test_stopwords_filtered(self):
        """Test builtin stopwords are filtered."""
        assert not _is_meaningful("img", 3)
        assert not _is_meaningful("dsc", 3)
        assert not _is_meaningful("final", 3)

    def test_custom_stopwords(self):
        """Test custom stopwords are filtered."""
        configure_slug(stopwords=["custom", "noise"])
        assert not _is_meaningful("custom", 3)
        assert not _is_meaningful("noise", 3)

    def test_whitelist_enforcement(self):
        """Test whitelist allows only specified tokens."""
        configure_slug(whitelist=["copper", "dormer", "chimney"])
        assert _is_meaningful("copper", 3)
        assert not _is_meaningful("random", 3)

    def test_numeric_only_filtered(self):
        """Test purely numeric tokens are filtered."""
        assert not _is_meaningful("12345", 3)

    def test_hex_strings_filtered(self):
        """Test long hex strings are filtered."""
        assert not _is_meaningful("c4a04fee", 3)
        assert not _is_meaningful("abcdef12", 3)

    def test_alphanumeric_mixed_allowed(self):
        """Test mixed alphanumeric with more letters than digits."""
        assert _is_meaningful("photo1", 3)  # 5 letters >= 1 digit: meaningful
        assert _is_meaningful("1photo", 3)  # 5 letters >= 1 digit: meaningful
        assert _is_meaningful(
            "123abc", 3
        )  # 3 letters >= 3 digits: meaningful (equal counts pass)
        assert not _is_meaningful("1234abc", 3)  # 3 letters < 4 digits: not meaningful


class TestDeduplication:
    """Test token deduplication."""

    def test_dedupe_preserves_order(self):
        """Test deduplication preserves first occurrence order."""
        result = _dedupe(["copper", "dormer", "copper", "finial"])
        assert result == ["copper", "dormer", "finial"]

    def test_dedupe_empty_list(self):
        """Test deduplication of empty list."""
        result = _dedupe([])
        assert result == []

    def test_dedupe_no_duplicates(self):
        """Test list without duplicates unchanged."""
        result = _dedupe(["one", "two", "three"])
        assert result == ["one", "two", "three"]


class TestSlugification:
    """Test slug string formatting."""

    def test_slugify_joins_with_hyphens(self):
        """Test tokens are joined with hyphens."""
        result = _slugify(["copper", "dormer", "installation"])
        assert result == "copper-dormer-installation"

    def test_slugify_removes_non_alnum(self):
        """Test non-alphanumeric characters removed except hyphens."""
        result = _slugify(["copper!", "dormer@", "test#"])
        assert result == "copper-dormer-test"

    def test_slugify_collapses_multiple_hyphens(self):
        """Test multiple hyphens collapse to single hyphen."""
        result = _slugify(["copper", "", "", "dormer"])
        assert result == "copper-dormer"

    def test_slugify_strips_leading_trailing_hyphens(self):
        """Test leading and trailing hyphens are stripped."""
        result = _slugify(["", "copper", ""])
        assert result == "copper"


class TestConfiguration:
    """Test slug configuration functionality."""

    def test_configure_max_words(self):
        """Test max_words configuration limits slug length."""
        configure_slug(max_words=3, min_len=3, stopwords=[], whitelist=[])
        result = seo_friendly_name("one-two-three-four-five-six")
        tokens = result.replace(".jpg", "").split("-")
        assert len(tokens) <= 3

    def test_configure_prefix(self):
        """Test prefix configuration prepends to slug."""
        configure_slug(
            prefix="best-dumpster-rental", min_len=3, stopwords=[], whitelist=[]
        )
        result = seo_friendly_name("tampa-service")
        assert result.startswith("best-dumpster-rental")

    def test_configure_location(self):
        """Test location configuration added to slug."""
        configure_slug(
            location="Tampa", prefix="", min_len=3, stopwords=[], whitelist=[]
        )
        result = seo_friendly_name("dumpster-rental")
        assert "tampa" in result

    def test_configure_prefix_and_location(self):
        """Test prefix and location both work together."""
        configure_slug(
            prefix="best-service",
            location="ann-arbor",
            min_len=3,
            stopwords=[],
            whitelist=[],
        )
        result = seo_friendly_name("custom-work")
        assert "best" in result and "service" in result
        assert "ann" in result and "arbor" in result

    def test_configure_multipart_names(self):
        """Test multipart names like 'send-out-cards' are preserved."""
        configure_slug(prefix="send-out-cards", location="celebration", min_len=3)
        result = seo_friendly_name("test-image")
        # Should contain components from both prefix and location
        assert "send" in result or "out" in result or "cards" in result
        assert "celebration" in result


class TestSlugTokenExtraction:
    """Test full token extraction pipeline."""

    def test_slug_tokens_from_clean_name(self):
        """Test extracting tokens from clean filename."""
        configure_slug(prefix="", location="", min_len=3, stopwords=[], whitelist=[])
        tokens = _slug_tokens_from_name("copper-dormer-installation")
        assert "copper" in tokens
        assert "dormer" in tokens
        assert "installation" in tokens

    def test_slug_tokens_respects_max_words(self):
        """Test token extraction respects max_words limit."""
        configure_slug(max_words=2, min_len=3, stopwords=[], whitelist=[])
        tokens = _slug_tokens_from_name("one-two-three-four")
        assert len(tokens) <= 2

    def test_slug_tokens_with_prefix_location(self):
        """Test prefix and location appear first in token list."""
        configure_slug(
            prefix="brand", location="city", min_len=3, stopwords=[], whitelist=[]
        )
        tokens = _slug_tokens_from_name("product-name")
        # Prefix/location should appear before content tokens
        first_two = tokens[:2]
        assert "brand" in first_two or "city" in first_two


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_filename(self):
        """Test very long filename gets truncated."""
        long_name = "-".join([f"word{i}" for i in range(20)])
        configure_slug(max_words=6, min_len=3)
        result = seo_friendly_name(long_name)
        tokens = result.replace(".jpg", "").split("-")
        assert len(tokens) <= 6

    def test_filename_with_only_numbers(self):
        """Test filename with only numbers returns default."""
        result = seo_friendly_name("12345678")
        assert result == "image.jpg"

    def test_filename_with_special_characters(self):
        """Test special characters are handled."""
        result = seo_friendly_name("copper!@#dormer$%^installation")
        assert result.endswith(".jpg")
        assert "copper" in result
        assert "dormer" in result

    def test_case_insensitive_processing(self):
        """Test processing is case-insensitive."""
        result1 = seo_friendly_name("Copper-Dormer")
        result2 = seo_friendly_name("copper-dormer")
        assert result1 == result2

    def test_unicode_handling(self):
        """Test basic Unicode characters are handled gracefully."""
        # Should not crash, may strip non-ASCII
        result = seo_friendly_name("café-copper-dormer")
        assert result.endswith(".jpg")

    def test_reset_configuration(self):
        """Test configuration can be reset/changed."""
        configure_slug(prefix="first", location="loc1")
        result1 = seo_friendly_name("test")

        configure_slug(prefix="second", location="loc2")
        result2 = seo_friendly_name("test")

        assert result1 != result2
        assert "second" in result2
        assert "loc2" in result2


@pytest.mark.parametrize(
    "input_name,expected_contains",
    [
        ("IMG_1234_copper_dormer", ["copper", "dormer"]),
        ("DSC_2025_custom_finial", ["custom", "finial"]),
        ("PXL_final_edited_chimney", ["chimney"]),
        ("screenshot_2025-08-16_work", ["work"]),
    ],
)
def test_real_world_filenames(input_name, expected_contains):
    """Test real-world filename patterns."""
    configure_slug(min_len=3, stopwords=[], whitelist=[])
    result = seo_friendly_name(input_name)
    for word in expected_contains:
        assert word in result
