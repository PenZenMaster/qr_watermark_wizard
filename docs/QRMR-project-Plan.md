# 🧠 QR Watermark Wizard – Project Enhancement Plan

**Author:** George Penzenik – Rank Rocket Co  
**Version:** v1.07.31 (UI) / v1.07.15 (Engine)  
**Updated:** 2025-08-25  
**Status:** Production Ready → Enhancement Phase

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

### 🎯 Priority 2: Core Engine Improvements
- **Multi-format Output Support**: Add PNG/WEBP output options (currently JPG only)
- **Watermark Templates**: Save/load watermark configurations for different clients
- **Advanced Positioning**: Custom QR/text positioning (not just upper-right/lower-left)
- **Batch Operation Logging**: Detailed processing logs with error tracking

### 🎨 Priority 3: UI/UX Enhancements
- **Real-time Preview Updates**: Live preview as user adjusts settings
- **Drag & Drop Interface**: Drop images directly into application
- **Progress Indicators**: Enhanced progress bars with file-by-file status
- **Recent Projects**: Quick-load recent client configurations

### 🔧 Priority 4: Professional Features
- **Cloud Storage Integration**: Direct upload to AWS S3/Google Drive
- **API Endpoint**: REST API for automated processing
- **Workflow Automation**: Watch folder auto-processing
- **Quality Metrics**: Image quality analysis and optimization

### 📊 Priority 5: Business Intelligence
- **Usage Analytics**: Track processing volume and client patterns
- **A/B Testing**: Compare different watermark configurations
- **Client Dashboard**: Web interface for non-technical users
- **Bulk Configuration**: CSV-driven batch settings

---

## 🛠️ Implementation Roadmap: AI Image Generation

### Phase 1: Foundation (Week 1-2)
**New Dependencies:**
```python
# requirements.txt additions
requests>=2.28.0          # HTTP API calls
aiohttp>=3.8.0           # Async HTTP for MCP
openai>=1.0.0            # OpenAI DALL-E integration
anthropic>=0.8.0         # Claude MCP integration
```

**New Architecture Components:**
- `image_generation.py` - Core generation engine
- `generation_ui.py` - UI components for generation workflow
- `api_connectors/` - Modular API adapters (OpenAI, MCP, etc.)
- Extended `config/settings.json` with generation parameters

### Phase 2: Core Features (Week 3-4)
**New UI Components:**
- `GenerationTab` class extending existing `QTabWidget`
- `ImagePreviewGrid` dialog for generated image review
- `GenerationParametersForm` for aspect ratio/quality controls
- `RevisionDialog` for prompt refinement workflow

**Integration Points:**
- Extend `WatermarkWizard` class with generation tab
- Reuse existing `QThread` pattern for async API calls
- Connect generation output to existing `input_images/` pipeline
- Add generation history to existing settings management

### Phase 3: Advanced Features (Week 5-6)
- Multi-provider API switching
- Batch generation workflows
- Generation template saving/loading
- Cost tracking and usage analytics

---

## 🛠️ Technical Debt & Maintenance

### Immediate (Next Session)
- **AI Integration Prerequisites**: Add async HTTP libraries and API clients
- **UI Architecture Review**: Plan tab-based interface extension
- **Configuration Schema**: Extend settings.json for generation parameters
- **Error Handling**: Design robust API failure handling

### Medium Term
- **Type Safety Audit**: Complete mypy compliance across all modules
- **Unit Testing**: Add pytest coverage for generation workflows
- **Documentation**: API integration guides and user workflows
- **Packaging**: Include AI dependencies in standalone executables

---

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
**Documentation & Architecture:** Claude Code  
**Quality Assurance:** Python toolchain (ruff, black, mypy, pytest)

