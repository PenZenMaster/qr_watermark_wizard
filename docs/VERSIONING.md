# Semantic Versioning Strategy

**QR Watermark Wizard** follows [Semantic Versioning 2.0.0](https://semver.org/)

## Version Format: MAJOR.MINOR.PATCH

### MAJOR version (X.0.0)
Increment when making incompatible API changes or major feature additions:
- Breaking changes to public APIs
- Major architectural changes
- New major features that significantly change user workflow
- Examples:
  - v1.0.0 → v2.0.0: Added AI image generation feature
  - Removal of deprecated features
  - Complete UI redesign

### MINOR version (X.Y.0)
Increment when adding functionality in a backward-compatible manner:
- New features that don't break existing workflows
- New configuration options
- New export formats
- Examples:
  - v2.0.0 → v2.1.0: Added S3 upload integration
  - v2.1.0 → v2.2.0: Added watch folder automation
  - New watermark templates

### PATCH version (X.Y.Z)
Increment for backward-compatible bug fixes:
- Bug fixes
- Performance improvements
- Documentation updates
- Security patches
- Examples:
  - v2.1.0 → v2.1.1: Fixed QR code opacity issue
  - v2.1.1 → v2.1.2: Improved error handling for missing files

## Version Update Protocol

### When to Bump Versions

**MAJOR (X.0.0):**
- AI image generation integration (v1.x → v2.0.0)
- Multi-client YAML profile system
- Provider adapter architecture
- Any change requiring user migration or workflow changes

**MINOR (X.Y.0):**
- S3/cloud storage upload
- REST API endpoint
- Watch folder automation
- Additional image format support
- New UI tabs or workflows

**PATCH (X.Y.Z):**
- Bug fixes
- UI tweaks
- Performance optimizations
- Documentation updates

### Files to Update

When bumping versions, update the version string in:
1. `main_ui.py` - Version field in module header
2. `qr_watermark.py` - Version field in module header
3. `docs/QRMR-project-Plan.md` - Version in header
4. `docs/STARTUP_CONTEXT.md` - Version field
5. Add version notes to module Comments sections

### Branch and Commit Strategy

**Development Workflow:**
- `main` branch: Stable releases only
- Feature branches: `feature-name` (e.g., `ai-image-generation`)
- Hotfix branches: `hotfix-description`

**Commit Messages (Conventional Commits):**
```
feat: add new feature (MINOR bump when merged)
fix: bug fix (PATCH bump when merged)
perf: performance improvement (PATCH bump)
refactor: code refactoring (PATCH bump)
test: add/update tests (PATCH bump)
docs: documentation updates (PATCH bump)
chore: maintenance tasks (PATCH bump)
BREAKING CHANGE: (MAJOR bump - include in commit body)
```

## Version History

### v2.0.0 (2025-12-24) - CURRENT DEVELOPMENT
**Branch**: ai-image-generation
- MAJOR: Added comprehensive unit testing framework (105 tests)
- MAJOR: Preparing AI image generation integration
- MAJOR: Implemented semantic versioning
- MINOR: Lean startup improvements (STARTUP_CONTEXT.md, optimized workflows)
- MINOR: Config/settings.json now gitignored for per-deployment configs

### v1.07.31 (2025-08-25) - STABLE
**Branch**: main
- PATCH: Fixed Pylance errors
- PATCH: Added editable slug_prefix and slug_location UI fields
- PATCH: Enhanced UX with multipart name support

### v1.07.15 (2025-08-01)
- MINOR: Added SEO-friendly filename option

### v1.07.14
- PATCH: Fixed output file extensions (PNG → JPG conversion)

## Pre-Release Versions

When developing features, use pre-release identifiers:
- `v2.0.0-alpha.1` - Early development
- `v2.0.0-beta.1` - Feature complete, testing phase
- `v2.0.0-rc.1` - Release candidate

## Changelog

Maintain `CHANGELOG.md` with:
- Version number and date
- Categories: Added, Changed, Deprecated, Removed, Fixed, Security
- User-facing changes only (not internal refactoring)

## Tags and Releases

**Git Tags:**
- Create annotated tags for releases: `git tag -a v2.0.0 -m "Release v2.0.0: AI Image Generation"`
- Push tags: `git push origin v2.0.0`

**GitHub Releases:**
- Create release notes from CHANGELOG
- Attach compiled binaries if applicable
- Link to documentation

## Migration Notes

When MAJOR version changes require migration:
1. Document breaking changes in CHANGELOG
2. Provide migration guide in docs/
3. Consider deprecation warnings in previous MINOR version
4. Update user documentation

---

**Current Version**: v2.0.0-dev
**Next Planned Release**: v2.0.0 (AI Image Generation)
**Last Stable**: v1.07.31
