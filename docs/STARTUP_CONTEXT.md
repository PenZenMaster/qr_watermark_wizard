# QR Watermark Wizard - Startup Context

**Last Updated:** 2025-12-26 17:30
**Branch:** main
**Commit:** c0591d5

---

## Last 3 Accomplishments

1. **Complete Ratio Refactor (BREAKING)** - Removed ALL ratio measurements (qr_size_ratio, font_size_ratio, text_padding_bottom_ratio, qr_padding_vh_ratio). Replaced with direct pixel/point values across entire codebase (qr_watermark.py, config_schema.py, main_ui.py, all profile YAMLs, all tests). User workflow restored - can now preview font sizes in points (72pt) instead of confusing ratios (0.05).

2. **AI Generation Auto-Save** - Fixed issue where generated images were only in memory. Added `_auto_save_generated_images()` method that auto-saves to `generation_output_dir` immediately after generation. Success message now shows save location.

3. **v3.0.0 Release** - Added Skippy the Magnificent to Help -> About dialog (custom QDialog with scaled image). Updated all version references to v3.0.0. Committed, pushed, and checkpointed.

---

## Next 3 Priorities

1. **User QA Testing** - Verify watermarking works correctly with direct pixel/point values on real images

2. **Profile System Testing** - Test creating/editing profiles with new pixel/point spinboxes in profile editor

3. **Documentation Update** - Update README.md with v3.0.0 breaking changes and migration notes if needed

---

## Current State

**Git Status:** Clean working tree, all changes committed and pushed
**Tests:** 167/167 passing (pytest)
**Quality Gates:** All passing (ruff, black, mypy)
**Branch:** main (up to date with origin/main)

**Blockers:** None

---

## Key Context Notes

1. **BREAKING CHANGE:** All ratio fields removed from WatermarkConfig dataclass. Existing profiles MUST use new field names (qr_size, font_size, text_padding, qr_padding) or app will fail to load.

2. **Profile YAML Migration:** All 3 existing profiles updated (default-client, easy-dumpster-rental, easy-dumpster-sarasota-fl). Any new profiles created externally must use pixel/point fields.

3. **Auto-Save Behavior:** AI generation now auto-saves immediately to `generation_output_dir`. Images still show in preview grid and can be manually saved or sent to watermark input directory.
