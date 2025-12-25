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
* No emojis or other Unicode in source code or test output that would fail in a Windows environment.
* Use ASCII alternatives: PASS/FAIL instead of ✅/❌, [INFO] instead of 🔵, etc.
* All print statements must use ASCII-safe characters only.

---

## 1) Session Commands (exact phrases to use)

### ▶️ `QRMR start`

**Goal:** Prime context at the start of a session efficiently (OPTIMIZED - 90% faster).
**Claude should:**

1. **Read lightweight context file** (single source of truth):

   * `docs/STARTUP_CONTEXT.md` (~40 lines, <3KB - contains everything needed)

   **OPTIONAL** - Only if user requests deep history:
   * Latest `docs/archive/checkpoints/CheckPoint-*.md` (detailed checkpoint)
   * `docs/projectStatus.md` (full project history)

2. **Post a kickoff note** with:

   * **Last session wins** (from STARTUP_CONTEXT - 3 bullet points)
   * **Next priorities** (from STARTUP_CONTEXT - 3 concrete steps)
   * **Current state** (branch, tests, blockers)
   * **Critical alerts** (any blockers or urgent issues)

3. **Confirm environment status**:
   * Git branch/status (from STARTUP_CONTEXT)
   * Working tree state (run git status to verify)
   * Any uncommitted changes or merge conflicts

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
4. **WAIT for user QA testing confirmation before commits** - Only proceed with git operations after user confirms QA results
5. `git add -A && git commit -m "chore(checkpoint): YYYY-MM-DD_HHMM – <short summary>" && git push` (only after QA confirmation)
6. Reply in chat with a 1‑paragraph summary + a checklist of next steps.

> **Trigger words**: “checkpoint now”, “prepare for rollover”, “juice check”, “save state” → run **QRMR checkpoint** immediately.

### ⏹️ `QRMR shutdown`

**Goal:** End a session cleanly with lightweight context capture (OPTIMIZED - 90% faster).
**Claude should:**

1. **Update Lightweight Context File**:
   - Generate `docs/STARTUP_CONTEXT.md` (~40 lines, <3KB) with:
     * **Last Updated** timestamp and branch
     * **Last 3 Accomplishments** (bullet points only)
     * **Next 3 Priorities** (concrete actionable steps)
     * **Current State** (git status, tests, blockers)
     * **Key Context Notes** (2-3 important details)

   **Template**: Use existing STARTUP_CONTEXT.md as reference

2. **Run Standard QRMR checkpoint** (OPTIONAL - only if user requests or major milestone):
   - Create checkpoint in `docs/archive/checkpoints/`
   - Use template from original QRMR checkpoint spec
   - Update `docs/projectStatus.md` with session summary

3. **Ensure all changes are committed and pushed**:
   - Verify git status is clean
   - Echo branch, commit hash, and tag if created

4. **Post "Shutdown complete"** with:
   - **3 priority bullets** for next session startup
   - Confirmation that STARTUP_CONTEXT.md is updated
   - Any pending user decisions or blockers

---

## 2) Project Guardrails (QR Watermark Wizard specifics)

* **Core Stack**: Python 3.9+, PyQt6, PIL/Pillow, qrcode library
* **AI Integration**: OpenAI API, Claude MCP, aiohttp for async API calls
* **Architecture**: Main UI (`main_ui.py`) + Watermark Engine (`qr_watermark.py`) + SEO Slug Generator (`rename_img.py`)
* **Workflow**: AI Image Generation → Preview/Review → Accept → QR Watermarking → SEO Renaming
* **Configuration**: JSON-based settings with client-specific watermark templates
* **Threading**: QThread for async processing (UI responsiveness during batch operations)
* **File Handling**: Collision detection, recursive folder processing, multiple image formats
* **Idempotency**: Safe reruns (dedupe by filename, skip already-processed images)
* **Performance**: Keep UI responsive; avoid blocking calls; use QThread for I/O operations

### Refactoring & Code Lifecycle Rules

* **DO NOT RENAME modules** when refactoring unless the rename is required to bring the rest of the codebase into sync to use or call the correct modules.
* **DELETE obsolete code** immediately: If a code module becomes obsolete as a result of a refactor, DELETE the obsolete code as part of the commit of the QA-accepted code. Do not leave dead/unused modules in the codebase.

---

## 3) Files & Paths (authoritative)

**Core Application:**
* **Main UI**: `main_ui.py` (PyQt6 WatermarkWizard class)
* **Watermark Engine**: `qr_watermark.py` (PIL-based processing)
* **SEO Slug Generator**: `rename_img.py` (filename optimization)
* **UI Definitions**: `ui/designer_ui.py` (Qt Designer output)
* **Configuration**: `config/settings.json` (runtime settings)

**Documentation & Management:**
* **Startup Context**: `docs/STARTUP_CONTEXT.md` (lightweight session context - PRIMARY for QRMR start)
* **Project Plan**: `docs/QRMR-Project-Plan.md` (source of truth + Design Variations - read only if needed)
* **Status**: `docs/projectStatus.md` (sprint state + full history - optional read)
* **Checkpoints**: `docs/archive/checkpoints/` (detailed checkpoints - optional, milestone only)

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
