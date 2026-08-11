# Scholarly Korean→English mode

This fork adds a conservative scholarly-translation layer without replacing the upstream general-book pipeline.

## Phase 1: Integrity
- citation protection/restoration
- LOCKED/PREFERRED/FLEXIBLE terminology contracts
- epistemic-strength audit
- semantic audit contract
- global terminology consistency
- multi-axis QA

## Phase 2: Theory preservation
- `author_concepts.json` definitions and forbidden implications
- `claims.json` with modality, polarity, conditions, exceptions, and forbidden reformulations
- deterministic negation/condition/modality risk checks
- LLM theory-preservation contract
- constrained chapter harmonizer

Use `prompts/ko-en-scholar-translation.md` for KO→EN scholarly work. See `PHASE1_SKILL_ADDENDUM.md` and `PHASE2_SKILL_ADDENDUM.md` for orchestration rules. Upstream `glossary.py` remains intact for backward compatibility.
