# Phase 2.2 — Codex Translator → Claude Reviewer

Phase 2.2 makes the scholarly KO→EN workflow intentionally asymmetric.

## Roles

### Codex — Translator
Codex owns source normalization, scholarly preflight, terminology/concept/claim contracts, chunk translation, Phase 1/2 audits, retranslation of failed chunks, merge, citation restoration, and the first complete English draft.

Codex MUST finish by writing a machine-verifiable handoff:

- `<temp_dir>/SCHOLARLY_HANDOFF.json`
- `<temp_dir>/HANDOFF.md`

Create it with `scripts/scholarly_handoff.py create`. Record the Korean source, Codex draft, translation audit, terminology/concept/claim contracts, and chunk provenance. Mark `--fresh-translation` only when the LLM translation was actually regenerated; list any resumed/cached chunks with `--reused-chunk`.

Codex translator artifacts are immutable after handoff. If the translator must change them, generate a new handoff with updated hashes.

### Claude Code — Reviewer / Publication Editor
Claude Code consumes the Korean source, Codex English draft, scholarly contracts, translation audit, and the handoff. It MUST validate the handoff before review:

```bash
python3 scripts/scholarly_handoff.py validate <temp_dir>/SCHOLARLY_HANDOFF.json
```

Claude Code does not independently retranslate the manuscript from scratch. It reviews and edits the Codex draft against the Korean source.

Allowed change classes:
- semantic correction
- academic-English editing
- terminology-family consistency
- citation localization
- bibliography normalization
- duplicate/front-matter cleanup

Claude must not silently change LOCKED terminology, claim strength, negation, conditions, theoretical relations, or author-defined distinctions.

## Reviewer outputs

Claude Code writes three separate outputs, never overwriting the Codex draft:

1. `final-en.md` — reviewed publication candidate
2. `publication-audit.md` — publication-readiness gate
3. `review-changes.md` — auditable change log

Each substantive entry in `review-changes.md` should identify:
- location/chunk or section
- BEFORE
- AFTER
- reason
- change type
- whether meaning changed

Before declaring completion, run:

```bash
python3 scripts/reviewer_gate.py <temp_dir>/SCHOLARLY_HANDOFF.json \
  --final-en <final-en.md> \
  --publication-audit <publication-audit.md> \
  --review-changes <review-changes.md>
```

A failed handoff hash, missing reviewer output, or invalid contract blocks completion.

## Publication readiness is separate from translation fidelity

`translation-audit.md` answers whether the Korean argument survived translation.

`publication-audit.md` answers whether the reviewed English manuscript is ready for a target publication context. It should check at minimum:
- remaining Korean text outside intentionally preserved bibliography/source material
- citation localization and spacing
- bibliography normalization policy
- duplicate abstracts/front matter
- terminology-family drift
- academic-English fluency
- source/claim fidelity after editorial changes

A manuscript can pass translation fidelity while still fail publication readiness.

## Shared-directory rule

A shared R drive is supported, but the handoff is the authoritative boundary. Claude must not treat the presence of output chunks or a prior final translation as proof of a fresh independent translation. Provenance in `SCHOLARLY_HANDOFF.json` records which chunks were freshly translated, retranslated, or reused.

Independent A/B model comparisons require separate temp directories and `fresh_translation=true` on both runs. Routine production should use the split workflow instead: Codex translates once; Claude reviews once.
