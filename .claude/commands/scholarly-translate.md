Translate a Korean scholarly document into publication-grade academic English using the repository's scholarly integrity and theory-preservation layers.

Required workflow:
1. Use the normal `translate-book` conversion/chunk/manifest/resume machinery.
2. Force source language `ko`, target language `en`, and scholarly mode.
3. Read and obey `PHASE1_SKILL_ADDENDUM.md`, `PHASE2_SKILL_ADDENDUM.md`, and `SCHOLARLY_TRANSLATION.md` before launching translation subagents.
4. Use `profiles/ko-en-humanities.json` unless the user supplies another scholarly profile.
5. Protect citations before translation; restore and validate them after translation.
6. Treat LOCKED terminology as immutable.
7. Run semantic, epistemic, claim, concept, negation/condition, relation, and global-consistency audits.
8. Retranslate failed chunks once with explicit audit findings; do not silently rewrite failed output in the auditor.
9. Harmonize only after all chunk-level critical checks pass, then rerun all critical checks.
10. Do not publish/build final artifacts when a blocking QA axis fails.

User request: $ARGUMENTS
