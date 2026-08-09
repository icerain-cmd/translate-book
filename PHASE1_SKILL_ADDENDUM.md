# Phase 1 — Scholarly KO→EN integrity layer

When source is Korean and target is English for academic/scholarly translation: run `scholarly_preflight.py`; load `terminology.json` v3 when present; protect citation spans before translation; use `prompts/ko-en-scholar-translation.md`; restore citations strictly; run epistemic and semantic audits; retry a failed chunk once; after merge run global locked-terminology consistency; emit multi-axis QA. Never auto-mark an extracted term LOCKED: only author/user configuration may do so.
