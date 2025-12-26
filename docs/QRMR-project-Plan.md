# 🧠 QR Watermark Wizard – Project Enhancement Plan

**Author:** George Penzenik – Rank Rocket Co
**Version:** v2.0.0 (Application-wide - Semantic Versioning)
**Updated:** 2025-12-24
**Status:** Development Branch - AI Image Generation Feature

---

## 📦 Current Application State

**Stable Production Features:**
- **QR code watermarks** and **multi-line text overlays** with shadow effects
- **SEO-friendly filename generation** with collision handling
- **Professional PyQt6 GUI** with preview, batch processing, and configuration
- **Recursive folder processing** with counter/timestamp collision strategies
- **Font customization** via QFontComboBox with size/color controls
- **Export mapping CSV** for filename tracking

**Current Client:** Salvo Metal Works (copper dormer specialist)

---

## 🧩 Project Structure

```plaintext
.
├── main_ui.py           ← GUI controller
├── qr_watermark.py      ← QR + text processing engine
├── rename_img.py        ← Slug generator
├── config/
│   └── settings.json     ← User settings
├── ui/
│   └── designer_ui.py    ← Qt Designer UI
```

---

## 🔹 main_ui.py — UI Controller

**Role:**
Main PyQt6 GUI that coordinates watermarking logic and config I/O.

**Responsibilities:**
- Loads and saves `settings.json`
- Provides custom-styled sliders, font selectors, and color pickers
- Supports SEO preview, recursive folder handling, and collision strategies
- Spawns watermarking thread to avoid UI freeze
- Injects additional dynamic UI elements:
  - `Preview SEO Names`, `Export Mapping CSV`, recursion checkbox, collision strategy

**Core Components:**
- `WatermarkWizard` class (QMainWindow)
- `WatermarkThread` (QThread for async batch processing)
- `update_config_from_ui()`, `preview_seo_names()`, `export_mapping_csv()`

---

## 🔹 qr_watermark.py — Watermark Engine

**Role:**
Adds branded overlays to images using PIL.

**Responsibilities:**
- Loads config via `refresh_config()`
- Creates QR code with `qrcode` and overlays it (upper-right)
- Draws styled multiline text (bottom-left)
- Respects ICC/exif preservation
- Outputs `.jpg` images using unique filenames
- Optional in-memory mode for UI previews (`return_image=True`)

**Highlights:**
- Supports QR sizing, opacity, and padding ratios
- Text and shadow color customization
- Filename SEO slugging via `seo_friendly_name()`

---

## 🔹 rename_img.py — Slug Engine

**Role:**
Converts long/ugly filenames into short, SEO-optimized slugs.

**Responsibilities:**
- Configurable via `configure_slug()`
- Filters out noise (UUIDs, timestamps, camera prefixes)
- Tokenizes filename and applies:
  - Min length filter
  - Stopwords
  - Whitelist rules
- Supports prefix/location injection
- Ensures `.jpg` extension

**Function:**
```python
seo_friendly_name("IMG_20230816_pxl_final-edit")
→ "brand-location-widget.jpg"
```

---

## ⚙️ Component Flow

```mermaid
flowchart TD
    subgraph UI Layer
        A[main_ui.py] -->|User Input| B[settings.json]
        A --> C[WatermarkThread]
        A -->|SEO Preview| E[rename_img.py]
    end

    subgraph Processing Layer
        C --> D[qr_watermark.py]
        D -->|Reads Config| B
        D -->|Calls| E
    end

    B -->|refresh_config()| D
    A -->|Preview| D
    E -->|configure_slug()| B
```

---

## 🚀 Enhancement Opportunities for Next Development Phase

### 🎯 PRIORITY 1: AI Image Generation Integration

**Requested Enhancement:** Full AI-powered image generation workflow before watermarking

**Core Features:**
- **API/MCP Integration**: Connect to image generation systems (OpenAI DALL-E, Midjourney, Stable Diffusion, Claude MCP)
- **Generation Parameters**: User-controlled aspect ratio, quality settings, size limits
- **Preview & Review System**: Grid preview of generated images with accept/reject workflow
- **Revision Loop**: Request refinements for rejected images with modified prompts
- **Auto-Input Pipeline**: Accepted images automatically moved to `input_images/` folder

**Architecture Approach:**
- **Compatible with Current Stack**: Extend existing PyQt6 interface with new tabs/dialogs
- **New Module**: `image_generation.py` - API connector and generation manager
- **UI Extension**: Add "Generate Images" tab to existing `WatermarkWizard` window
- **Thread Integration**: Use existing `QThread` pattern for async API calls

### 🔧 Priority 2: Professional Features
- **Cloud Storage Integration**: Direct upload to AWS S3/Google Drive
- **API Endpoint**: REST API for automated processing
- **Workflow Automation**: Watch folder auto-processing
- **Quality Metrics**: Image quality analysis and optimization

### 🎯 Priority 3: Core Engine Improvements
- **Multi-format Output Support**: Add PNG/WEBP output options (currently JPG only)
- **Watermark Templates**: Save/load watermark configurations for different clients
- **Advanced Positioning**: Custom QR/text positioning (not just upper-right/lower-left)
- **Batch Operation Logging**: Detailed processing logs with error tracking

### 🎨 Priority 4: UI/UX Enhancements
- **Real-time Preview Updates**: Live preview as user adjusts settings
- **Drag & Drop Interface**: Drop images directly into application
- **Progress Indicators**: Enhanced progress bars with file-by-file status
- **Recent Projects**: Quick-load recent client configurations
---

## 🛠️ Implementation Roadmap: AI Image Generation

### Phase 1:
## 🛠️ Technical Debt & Maintenance


## 💼 Current Client Configuration

**Salvo Metal Works Setup:**
- Target: https://salvometalworks.com/product-category/custom-dormers/
- Branding: White text, black shadow, Roboto font
- SEO Focus: "salvo-chicago-[copper/dormer/metalwork]"
- Contact: (866) 713-3396, info@salvometalworks.com

**Recent Processing:** 9 input images → 8 watermarked outputs (copper dormer focus)

---

## 🎯 Success Metrics

**Current State:** Stable production tool with professional UI
**AI Enhancement Goals:**
- **Generation Integration**: Support 3+ AI image generation providers (OpenAI, Claude MCP, Stable Diffusion)
- **User Workflow**: Complete generate → review → revise → accept → watermark pipeline
- **Performance**: Generate and preview 4-10 images within 30 seconds per request
- **Quality Control**: User acceptance rate >80% for generated images

**Existing Enhancement Goals:**
- 50% faster batch processing through optimization
- Support 5+ output formats beyond JPG
- Template system supporting 10+ client configurations
- API capability for automated workflows

---

## ✨ Development Team

**Lead Engineer:** George Penzenik (Rank Rocket Co)
**Documentation & Architecture:** George Penzenik
**Quality Assurance:** Python toolchain (ruff, black, mypy, pytest)

---

## ✅ Architecture Update (2025-12-24): YAML Profiles, AI Generation, Automation, S3 Upload

This update extends the tool from a single `settings.json` configuration into a **multi-client, YAML-driven workflow**
that supports:
- Generate → QC → Watermark → Upload (S3) pipeline
- User-selectable input/output directories (per profile)
- Multiple saved client profiles (recent projects + quick load)
- Provider-pluggable image generation with adapter interface
- Automation-ready CLI runner + watch-folder mode

### 🧱 Concrete Module / File Tree (Proposed)

```plaintext
Folder PATH listing for volume TOSHIBA EXT
Volume serial number is B0D0-A4E4
E:.
│   .gitignore
│   launch_designer.bat
│   PlayfairDisplay-Regular.ttf
│   main_ui.py
│   qr_watermark.py
│   rename_img.py
│   pipeline_runner.py
│   tree.txt
│
├── config
│   ├── profiles
│   │   ├── salvo_metal_works.yaml
│   │   └── easy_dumpster_tampa.yaml
│   ├── app_settings.json
│   └── providers.yaml
│
├── input_images
│   └── (user-selected at runtime; optional default folder)
│
├── generated_images
│   └── (user-selected at runtime; optional default folder)
│
├── output_images
│   └── (user-selected at runtime; optional default folder)
│
├── logs
│   └── qrmr.log
│
├── ui
│   └── designer.ui
│
└── qrmr
    ├── __init__.py
    ├── config_schema.py
    ├── config_store.py
    ├── image_generation.py
    ├── provider_adapters.py
    ├── quality_control.py
    ├── uploader_s3.py
    ├── watch_folder.py
    └── utils.py
```

> Notes:
> - Move reusable logic into a package folder (`qrmr/`) to keep UI thin and automation clean.
> - Keep `qr_watermark.py` and `rename_img.py` as the stable engine modules; call them from `pipeline_runner.py`.

---

## 🔁 Configuration Architecture: settings.json → app_settings.json + YAML Profiles

### Why split?
The current `config/settings.json` mixes **client-specific job settings** (paths, NAP/QR/text overlays, slug rules) with
**application behavior** (recents, theme, automation defaults). See the current single-file config keys like
`input_dir`, `output_dir`, `qr_link`, and slug rules. fileciteturn3file0L1-L58

### Proposed split
1) **App-level settings** (shared across all clients):
- UI preferences (theme, recent profiles)
- default folders (optional)
- automation defaults (watch-folder settings)
- last-used profile pointer

2) **Client profile YAML** (one file per client/location/campaign):
- generation paths (where AI images land)
- watermark settings
- SEO naming rules
- generation provider routing
- upload settings (S3 bucket/prefix)

### New config files
- `config/app_settings.json` (global app config)
- `config/profiles/<profile>.yaml` (one per client/campaign)
- `config/providers.yaml` (API keys + provider defaults; can also be env vars)

---

## 📄 YAML Profile Schema (v1)

Below is a **concrete** YAML profile example derived from the current JSON settings for the Tampa Dumpster campaign. fileciteturn3file0L1-L58

```yaml
{
  "profile": {
    "name": "Easy Dumpster Rental \u2014 Tampa FL",
    "slug": "easy-dumpster-tampa",
    "client_id": "easy_dumpster_rental",
    "created": "2025-12-24",
    "modified": "2025-12-24"
  },
  "paths": {
    "generation_output_dir": "D:/OneDrive/RankRocket/Clients/Adventure Marketing/EZ Dumpster/images/Tampa FL/original",
    "input_dir": "D:/OneDrive/RankRocket/Clients/Adventure Marketing/EZ Dumpster/images/Tampa FL/original",
    "output_dir": "D:/OneDrive/RankRocket/Clients/Adventure Marketing/EZ Dumpster/images/Tampa FL/watermarked",
    "archive_dir": "D:/OneDrive/RankRocket/Clients/Adventure Marketing/EZ Dumpster/images/Tampa FL/archive"
  },
  "generation": {
    "mode": "auto",
    "count": 4,
    "width": 512,
    "height": 512,
    "style": "photoreal",
    "text_strict": true,
    "exact_text": [
      "Easy Dumpster Rental Tampa FL",
      "(813) 400-1178"
    ],
    "max_attempts_per_image": 4,
    "timeout_seconds": 240
  },
  "providers": {
    "primary": "fal",
    "text_strict_provider": "ideogram",
    "fallback": "stability"
  },
  "watermark": {
    "qr_link": "https://easydumpsterrental.com/florida/dumpster-rental-tampa-fl",
    "qr_size_ratio": 0.15,
    "qr_opacity": 0.85,
    "qr_padding_vh_ratio": 0.01574074074074074,
    "text_overlay": "813-400-1178",
    "text_color": [
      255,
      255,
      255
    ],
    "shadow_color": [
      0,
      0,
      0,
      128
    ],
    "font_family": "Tahoma",
    "font_size_ratio": 0.05,
    "text_padding_bottom_ratio": 0.041666666666666664
  },
  "seo_naming": {
    "enabled": true,
    "process_recursive": false,
    "collision_strategy": "counter",
    "slug_prefix": "best-dumpster-rental",
    "slug_location": "Tampa",
    "slug_max_words": 4,
    "slug_min_len": 4,
    "slug_stopwords": [
      "simple",
      "compose",
      "remix",
      "beauty",
      "installation",
      "penzenmaster"
    ],
    "slug_whitelist": [
      "copper",
      "dormer",
      "finial",
      "chimney",
      "shroud",
      "custom",
      "historic",
      "home",
      "homes",
      "chicago",
      "york",
      "city",
      "lake",
      "front",
      "collection",
      "light",
      "cupola",
      "vane",
      "weather"
    ]
  },
  "upload": {
    "enabled": true,
    "provider": "aws_s3",
    "bucket": "rankrocket-public-assets",
    "prefix": "easy-dumpster/tampa-fl/",
    "acl": "public-read",
    "cache_control": "public, max-age=31536000, immutable"
  }
}
```

---

## 🔐 Provider Credentials Policy

- Client YAML profiles MUST NOT store API keys.
- Store provider keys in `config/providers.yaml` or environment variables.
- `providers.yaml` example (not checked into git):
```yaml
fal:
  api_key: "FAL_..."
ideogram:
  api_key: "IDEOGRAM_..."
stability:
  api_key: "STABILITY_..."
aws:
  access_key_id: "AKIA..."
  secret_access_key: "..."
  region: "us-east-1"
```

---

## 🧩 Provider Adapter Interface (Design)

### Provider Adapter Interface (Python)

All image providers must implement the same contract so the UI + pipeline can swap providers without changes.

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple

@dataclass(frozen=True)
class GenerateRequest:
    prompt: str
    negative_prompt: Optional[str]
    width: int
    height: int
    num_images: int
    style: Optional[str] = None
    seed: Optional[int] = None
    guidance: Optional[float] = None
    steps: Optional[int] = None
    # When text must be exact (e.g., signs/phone numbers)
    exact_text: Optional[List[str]] = None
    timeout_seconds: int = 240
    meta: Optional[Dict[str, Any]] = None  # provider-specific knobs

@dataclass(frozen=True)
class GeneratedImage:
    bytes: bytes
    mime_type: str  # "image/png", "image/jpeg", "image/webp"
    seed: Optional[int]
    provider: str
    model: Optional[str]
    warnings: List[str]
    meta: Dict[str, Any]

@dataclass(frozen=True)
class GenerateResult:
    images: List[GeneratedImage]
    request_id: Optional[str]
    raw: Dict[str, Any]  # raw provider response for logging/debug

class ImageProvider(Protocol):
    """Provider contract."""

    @property
    def name(self) -> str: ...

    def supports_styles(self) -> bool: ...
    def supports_exact_text(self) -> bool: ...
    def max_in_flight(self) -> int: ...

    def generate(self, req: GenerateRequest) -> GenerateResult:
        """Blocking call. Wrap in QThread/async executor in UI."""
        ...

class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, ImageProvider] = {}

    def register(self, provider: ImageProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> ImageProvider:
        return self._providers[name]

    def available(self) -> List[str]:
        return sorted(self._providers.keys())
```

Implementation notes:
- `image_generation.py` owns orchestration (provider routing, retries, saving images to disk).
- Individual adapters live in `provider_adapters.py` (FalProvider, IdeogramProvider, StabilityProvider).
- Provider credentials live in `config/providers.yaml` or environment variables (never in client profiles).
```


---

## 🧰 Multi-Client Support: Profile Store

### Requirements
- Save unlimited client profiles.
- Load by recent list and by search.
- Export/import a profile YAML.
- Maintain `last_used_profile` for quick startup.

### Implementation
- `qrmr/config_store.py` manages:
  - `profiles_dir` scanning
  - recent list (stored in app_settings.json)
  - validation against schema
- `qrmr/config_schema.py` provides:
  - dataclasses / pydantic-style validation
  - defaults + migrations (v1 → v2)

---

## 🤖 Automation Readiness

### CLI runner
Add `pipeline_runner.py`:
- `--profile config/profiles/easy_dumpster_tampa.yaml`
- `--generate` (optional)
- `--watermark` (default on)
- `--upload` (optional)

### Watch-folder (near-term)
`qrmr/watch_folder.py`:
- watches the generation output folder OR input folder
- triggers pipeline on new files
- writes logs + manifest

### Output manifest
Write `manifest.json` per run:
- input file → output file mapping
- S3 URLs if uploaded
- provider metadata (model, seed, request_id)
- QC results

---

## ✅ Updates to Existing Enhancement Priorities

### Priority 1 (AI Generation Integration)
- Expand `image_generation.py` to support **provider routing**:
  - If `text_strict: true`, use Ideogram
  - Else use fal (primary)
  - Retry with Stability on failures
- Add auto-QC loop to reduce human curation

### Priority 2 (Professional Features)
- Implement `uploader_s3.py` + `pipeline_runner.py` first
- Add watch-folder next

### Priority 3 (Core Engine Improvements)
- Multi-format output is now a pipeline option (`output_format: jpg|png|webp`)
- Templates are now YAML profiles

### Priority 4 (UI/UX Enhancements)
- "Recent Projects" becomes recent profile list (multi-client)
- "Generate Images" tab writes images into `generation_output_dir` and can optionally auto-run pipeline
