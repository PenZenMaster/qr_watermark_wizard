# Claude Code – QR Watermark Wizard Playbook

> Project: **QR Watermark Wizard** · Purpose: Professional PyQt6 application for AI image generation, QR code watermarking, and SEO-friendly filename optimization with reliable session handoffs and checkpoints.

---

## 0) Mission & Working Agreement

When asked for changes in this repo:

1. **Plan** briefly (what/why/files to touch).
2. **Patch** with **small, reviewable diffs**; no broad rewrites unless asked.
3. **Test** using the quality gates in §4.
4. **Summarize** changes, risks, and next steps.
5. Respect the guardrails below.

**Non‑negotiables**

* Production‑ready diffs only (no placeholders or TODO litter in committed code).
* Preserve headers/license blocks; bump versions per project rules.
* No secrets in code; use `.env`/secure config.

---

## 1) Session Commands (exact phrases to use)

### ▶️ `QRMR start`

**Goal:** Prime context at the start of a session.
**Claude should:**

1. Read, if present (otherwise create stubs):

   * `docs/QRMR-Project-Plan.md`
   * Latest `docs/archive/checkpoints/CheckPoint-*.md`
   * `docs/projectStatus.md`
2. Post a **kickoff note** with:

   * **Last session wins** (bullets)
   * **What remains this sprint** (bullets)
   * **Today’s plan** (1–3 concrete steps)
3. Confirm Git branch/status and whether working tree is clean.

### 💾 `QRMR checkpoint`

**Goal:** Capture state at any time (especially near usage limits) so the next session can resume seamlessly.
**Claude should:**

1. Create a new checkpoint file in `docs/archive/checkpoints/` using the existing naming pattern if found; otherwise default to:
   `CheckPoint-YYYY-MM-DD_HHMM.md`
2. Use this template in the file:

   * **Context summary** (why we’re here)
   * **Accomplishments** (what shipped)
   * **Technical changes** (files touched, diffs overview)
   * **Known issues / blockers**
   * **Next session priorities** (bullet list)
   * **Backlog movement** (added/removed/deferred)
   * **Git status** (branch, last commit hash, pushed: yes/no)
3. Update live docs:

   * Append any **Design Variations & Rationale** to `docs/QRMR-Project-Plan.md`.
   * Update `docs/projectStatus.md` (Completed / In‑Progress / Deferred + Next items).
4. `git add -A && git commit -m "chore(checkpoint): YYYY-MM-DD_HHMM – <short summary>" && git push`
5. Reply in chat with a 1‑paragraph summary + a checklist of next steps.

> **Trigger words**: “checkpoint now”, “prepare for rollover”, “juice check”, “save state” → run **QRMR checkpoint** immediately.

### ⏹️ `QRMR shutdown`

**Goal:** End a session cleanly and **always** checkpoint.
**Claude should:**

1. Run **QRMR checkpoint** (mandatory).
2. Ensure all changes are pushed; echo branch, commit hash, and tag if created.
3. Post “Shutdown complete” with **3 bullets** for the next session.

---

## 2) Project Guardrails (QR Watermark Wizard specifics)

* **Core Stack**: Python 3.9+, PyQt6, PIL/Pillow, qrcode library
* **AI Integration**: OpenAI API, Claude MCP, aiohttp for async API calls
* **Architecture**: Main UI (`main_ui.py`) + Watermark Engine (`qr_watermark.py`) + SEO Slug Generator (`rename_img.py`)
* **Workflow**: AI Image Generation → Preview/Review → Accept → QR Watermarking → SEO Renaming
* **Configuration**: JSON-based settings with client-specific watermark templates
* **Threading**: QThread for async processing (UI responsiveness during batch operations)
* **File Handling**: Collision detection, recursive folder processing, multiple image formats

---

## 3) Files & Paths (authoritative)

**Core Application:**
* **Main UI**: `main_ui.py` (PyQt6 WatermarkWizard class)
* **Watermark Engine**: `qr_watermark.py` (PIL-based processing)
* **SEO Slug Generator**: `rename_img.py` (filename optimization)
* **UI Definitions**: `ui/designer_ui.py` (Qt Designer output)
* **Configuration**: `config/settings.json` (runtime settings)

**Documentation & Management:**
* **Project Plan**: `docs/QRMR-Project-Plan.md` (architecture + enhancement roadmap)
* **Status**: `docs/projectStatus.md` (current sprint state)
* **Checkpoints**: `docs/archive/checkpoints/` (session history)

**Processing Folders:**
* **Input Images**: `input_images/` (source images for watermarking)
* **Output Images**: `output_images/` (processed watermarked images)

> If these files/folders don't exist, Claude should create them with minimal scaffolding.

---

## 4) Code Quality Gates & Runbook

### Python

```bash
ruff --fix . && black . && mypy . && pytest -q
```

* Full typing on new/changed code; Google‑style docstrings.
* Use structured logging; no `print` in libraries.
* CLIs default to safe behavior (dry‑run when destructive).
* `pathlib` for filesystem ops; write OS‑portable code.

### PyQt6 UI Standards

* Proper type annotations for all Qt components
* Thread safety: UI updates only on main thread
* Resource management: proper cleanup of QPixmap and PIL Image objects
* Accessibility: keyboard navigation and screen reader support

---

## 5) Debug/Release Hygiene

Before tagging a release:

* Remove debug prints and traces from Python modules
* Test full workflow: Generate images → Preview → Watermark → Export
* Verify UI responsiveness during batch processing
* Test with different image formats (JPG, PNG, WEBP)
* Validate SEO slug generation with various filename patterns
* Check client configuration templates (Salvo Metal Works, etc.)

---

## 6) Override Directives (Add / Edit / Delete)

Change rules via chat without manually editing this file. Claude should apply the change, show a small diff, and commit.

### Add

```
ADD RULE → <Section Anchor>
<one sentence rule to append>
```

### Edit

```
EDIT RULE → <Section Anchor>
<existing line text>
--- becomes ---
<new line text>
```

### Delete

```
DELETE RULE → <Section Anchor>
<exact line text to remove>
```

**Section Anchors**:
`0) Mission` · `1) Session Commands` · `2) Project Guardrails` · `3) Files & Paths` · `4) Code Quality Gates` · `5) Debug/Release Hygiene` · `6) Override Directives`

---

## 7) Quick Prompts

* **Start session**: `QRMR start` (load plan, status, last checkpoint)
* **Checkpoint now**: `QRMR checkpoint` (save state, commit, push)
* **End session**: `QRMR shutdown` (mandatory checkpoint + 3 next steps)
* **Test quality**: `ruff --fix . && black . && mypy . && pytest -q`
* **Override rule**: `EDIT RULE → 4) Code Quality Gates …`

---

## 8) Notes on Continuity & Limits

* Use **QRMR checkpoint** whenever you're nearing your daily usage cap or switching tasks.
* A checkpoint is **mandatory** for every **QRMR shutdown**.
* Next session resumes with **QRMR start** which reads the last checkpoint and aligns the plan.

---

## 9) Current Version Status

* **UI Version**: v1.07.31 (main_ui.py)
* **Engine Version**: v1.07.15 (qr_watermark.py) 
* **Architecture**: Production-ready PyQt6 application
* **Active Client**: Salvo Metal Works (copper dormer specialist)
* **Next Major Feature**: AI Image Generation Integration (Priority 1)
