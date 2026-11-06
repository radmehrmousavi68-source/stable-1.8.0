# Stable-first integration plan

## Scope and baseline
- Stable source: `LocalChat_1_8_0_STABLE.zip`
- Feature source: `LocalChat-1.8.7-Plan-First-Programming.zip`
- Integration target: `merged-next` (never modify `main` during integration)
- Policy: preserve Stable behavior and APIs unless a specific feature requires a reviewed adapter or additive change.

## Reproduced baseline tests
Executed `python -m pytest -q` independently from each extracted archive:
- Stable 1.8.0: **90 passed, 21 subtests passed** (26.60s)
- GitHub 1.8.7: **106 passed, 26 subtests passed** (17.68s)

The Python startup emitted a non-fatal spreadsheet warmup warning in this environment after pytest completed. It did not change either pytest exit code (both were 0).

## Structural comparison
Stable-only or Stable-preserved modules/features:
- `models_catalog.py`, `settings.py`, `files.py`, `search_providers.py`
- `capability_docs/model_manager.md`, `vision.md`, `file_upload.md`
- Stable packaging specs, installer scripts and launcher entry points

New 1.8.7 feature modules:
- Persian speech normalization: `persian_speech.py`
- Speech workers: `tts_worker.py`, `stt_worker.py`
- System/programming tools and approval workflow: `system_tools.py`
- Docker test runtime: `docker_runtime.py`
- Attachment extraction/batch-analysis support: `attachment_parser.py`
- New setup scripts, feature documentation and associated tests

High-risk shared files:
- `local_chat/server.py` (Stable 2,169 lines; 1.8.7 2,849 lines; major route/lifecycle/streaming changes)
- `local_chat/static/app.js` (both versions changed substantially)
- `local_chat/static/index.html`, `style.css`, `launcher.py`, `start.bat`, `memory.py`, `test_server.py`

## Integration sequence
1. Additive feature modules and dependency review; do not replace Stable modules.
2. Add voice worker lifecycle behind explicit capability detection and isolated settings.
3. Add speech input/output UI as isolated controls, preserving existing chat and Stop behavior.
4. Add system-tool planning/approval using Stable's existing request/response and identity/security boundaries.
5. Add Docker runtime as opt-in, fail-closed functionality; never silently execute host commands.
6. Add attachment parser and batch analysis without replacing Stable's upload/storage implementation.
7. Integrate server routes through small adapters and regression tests.
8. Reconcile packaging, setup scripts, documentation and full regression tests.

## Safety gates
- Never wholesale replace Stable `server.py`, `app.js`, settings, model catalog, file handling or packaging.
- No external command execution without explicit approval, path validation, timeout and cleanup.
- Docker feature must report unavailable safely when Docker is absent; it must not fall back to unrestricted host execution.
- Voice workers must be independently stoppable and cleaned up on app shutdown.
- Preserve existing Ollama model discovery, model catalog, vision support, search, memory and file upload.
- Each stage must pass its focused tests plus the Stable regression suite before the next stage is committed.

## Current stage
Stage 1 (source inventory, baseline tests and integration plan) complete. No application runtime code has been changed yet.
