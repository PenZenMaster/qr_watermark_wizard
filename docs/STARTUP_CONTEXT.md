# QR Watermark Wizard - Startup Context

**Last Updated:** 2025-12-27 18:15
**Branch:** main
**Commit:** 1a753e4

---

## Last 3 Accomplishments

1. **Fixed Multi-Image Generation Bug** - Fal.ai FLUX.2 model doesn't support num_images parameter. Modified FalProvider to make multiple sequential API calls (1 per image). User QA confirmed: 4/4 images now generate and save successfully.

2. **Enhanced Provider Logging** - Added detailed download progress tracking across all providers (Fal, Ideogram, Stability). Shows success/failure for each image with file sizes and error details.

3. **Fixed Windows Path Issues** - Added os.path.normpath() to auto-save function to resolve Errno 22 (Invalid argument) caused by mixed forward/backward slashes in paths. Enhanced error diagnostics with full tracebacks.

---

## Next 3 Priorities

1. **Profile System Testing** - Test creating/editing profiles with new pixel/point spinboxes in profile editor (from v3.0.0 ratio refactor)

2. **Documentation Update** - Update README.md with v3.0.0 breaking changes and migration notes if needed

3. **User Feature Requests** - Address any new feature requests or bug reports from users

---

## Current State

**Git Status:** Clean working tree (config/settings.json has local user settings - not committed)
**Tests:** 167/167 passing (pytest)
**Quality Gates:** All passing (ruff, black, mypy, bandit)
**Branch:** main (up to date with origin/main)

**Blockers:** None

---

## Key Context Notes

1. **Multi-Image Generation**: FLUX.2 [flex] model requires multiple API calls for num_images > 1. Each image is a separate request. This is working correctly now with proper progress tracking.

2. **Path Normalization**: Windows systems require os.path.normpath() for paths with mixed slashes. Auto-save now handles this correctly.

3. **v3.0.0 Breaking Change**: All ratio fields removed from WatermarkConfig dataclass. Existing profiles MUST use new field names (qr_size, font_size, text_padding, qr_padding).
