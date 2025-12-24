# QR Watermark Wizard - Session Context

**Last Updated**: 2025-12-24
**Branch**: ai-image-generation
**Version**: v2.0.0
**Last Commit**: 2eba47c - test: add comprehensive unit testing framework

---

## Last 3 Accomplishments

- Comprehensive unit testing framework implemented (105 tests, all passing)
- Lean startup improvements from cloud-stack-generator integrated
- Version bumped to 2.0.0 and ai-image-generation branch created

---

## Next 3 Priorities

1. **AI Integration Phase 1**: Resume Priority 1 enhancement with dependencies setup
2. **UI Architecture Extension**: Continue tab-based interface design for AI generation
3. **API Connector Development**: Begin OpenAI DALL-E integration foundation

---

## Current State

**Git Status**: On branch ai-image-generation
**Tests**: 105 unit tests passing (pytest framework)
**Blockers**: None - ready for AI feature development

---

## Key Context Notes

- Current version: v2.0.0 (semantic versioning active)
- Active client: Salvo Metal Works (copper dormer specialist)
- Architecture: Production-ready PyQt6 application with test coverage
- Current focus: AI Image Generation Integration (v2.x development)
- Test framework: pytest with 105 passing tests
- Settings values auto-sync between UI and config/settings.json (now gitignored)
- Multipart names supported via hyphenated slugs

---

## Quick Reference

**Core Files**:
- `main_ui.py` - PyQt6 WatermarkWizard class
- `qr_watermark.py` - PIL-based watermark engine
- `rename_img.py` - SEO slug generator
- `config/settings.json` - Runtime configuration

**Workflow**: AI Generation → Preview/Review → Accept → QR Watermarking → SEO Renaming

**Quality Gate**: `ruff --fix . && black . && mypy . && pytest -q`
