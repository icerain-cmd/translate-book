---
description: Review a Codex scholarly Korean-to-English translation without retranslating from scratch.
argument-hint: <path-to-SCHOLARLY_HANDOFF.json>
---

Read `CLAUDE.md` and `PHASE2_2_HANDOFF.md`.

The argument is a Phase 2.2 `SCHOLARLY_HANDOFF.json` produced by Codex.

1. Validate the handoff with `python3 scripts/scholarly_handoff.py validate "$ARGUMENTS"`.
2. Treat the Korean source, Codex translation, terminology/concept/claim contracts, and translation audit named in the handoff as immutable inputs.
3. Do **not** independently retranslate the manuscript from scratch and do not overwrite the Codex draft.
4. Review the Codex draft against the Korean source for semantic fidelity, claim/negation/condition preservation, terminology-family consistency, and publication-quality academic English.
5. Perform publication editing that translation integrity intentionally did not do: citation localization, bibliography normalization as appropriate to the requested target style, duplicate abstract/front-matter cleanup, residual Korean-text review, and idiomatic academic-English editing.
6. Never silently change LOCKED terminology or author-defined theoretical relations. Any meaning-changing correction must be explicitly recorded.
7. Write sibling outputs named `final-en.md`, `publication-audit.md`, and `review-changes.md` unless the user specifies names.
8. `review-changes.md` must record location, BEFORE, AFTER, reason, change type, and whether meaning changed for substantive edits.
9. Run `scripts/reviewer_gate.py` against the handoff and all three outputs before declaring completion.
10. Report publication-readiness status separately from the Codex translation-fidelity result.
