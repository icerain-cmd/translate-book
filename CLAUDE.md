# CLAUDE.md

## Project

translate-book is a Claude Code Skill that translates books (PDF/DOCX/EPUB) into any language using parallel subagents. Published on ClawHub as `translate-book` and on GitHub as `deusyu/translate-book`.

## Scholarly KO→EN routing

When the request is specifically Korean → English and clearly academic/scholarly (for example a paper, journal article, thesis, dissertation, or an explicit `academic`/`scholarly` mode), route conservatively to the scholarly pipeline instead of the general translation prompt.

- Prefer `/scholarly-translate <request>` only when the user explicitly wants Claude Code itself to perform a standalone scholarly translation.
- For routine production, prefer the Phase 2.2 split workflow: **Codex Translator → Claude Reviewer**.
- If `SCHOLARLY_HANDOFF.json` is supplied or present for the manuscript, reviewer mode takes precedence over starting another full translation. Use `/scholarly-review <path-to-SCHOLARLY_HANDOFF.json>`.
- Run `python3 scripts/scholarly_dispatch.py --source-lang ko --target-lang en --mode scholarly --request "<user request>"` when routing is ambiguous.
- Read `PHASE1_SKILL_ADDENDUM.md`, `PHASE2_SKILL_ADDENDUM.md`, `PHASE2_2_HANDOFF.md`, and `SCHOLARLY_TRANSLATION.md` for scholarly work.
- Use `profiles/ko-en-humanities.json` by default unless the user supplies another scholarly profile.
- General Korean→English prose and all non-Korean-source translations must remain on the original general path.

## Phase 2.2 role: Claude Code is reviewer / publication editor

When a valid Codex `SCHOLARLY_HANDOFF.json` exists, Claude Code MUST NOT independently retranslate the Korean manuscript from scratch. Validate the handoff first:

```bash
python3 scripts/scholarly_handoff.py validate <temp_dir>/SCHOLARLY_HANDOFF.json
```

Treat the Korean source, Codex draft, contracts, and translation audit named in the handoff as immutable inputs. Review the Codex draft against the Korean source and make only traceable corrections or publication edits.

Allowed work includes semantic correction, academic-English editing, terminology-family consistency, citation localization, bibliography normalization, and duplicate/front-matter cleanup. Do not silently alter LOCKED terminology, claim strength, negation, conditions, theoretical relations, or author-defined distinctions.

Write three new reviewer outputs without overwriting Codex artifacts:

- `final-en.md`
- `publication-audit.md`
- `review-changes.md`

`review-changes.md` records location, BEFORE, AFTER, reason, change type, and whether meaning changed for substantive edits. Before declaring completion, run `scripts/reviewer_gate.py` with the handoff and all three outputs. Translation fidelity and publication readiness are separate gates.

## Structure

- `SKILL.md` — Skill definition, the orchestration logic that Claude Code / OpenClaw follows
- `scripts/convert.py` — PDF/DOCX/EPUB → Markdown chunks (via Calibre HTMLZ)
- `scripts/manifest.py` — SHA-256 chunk tracking and merge validation
- `scripts/glossary.py` — Term-consistency glossary; per-chunk term tables injected into sub-agent prompts
- `scripts/chunk_context.py` — Read-only previous/next chunk excerpts injected into sub-agent prompts
- `scripts/meta.py` — Per-chunk sub-agent observation file schema
- `scripts/merge_meta.py` — Batch-boundary merge of sub-agent observations into the canonical glossary
- `scripts/run_state.py` — Selective re-translation planner and run_state.json recorder
- `scripts/merge_and_build.py` — Merge translated chunks → HTML/DOCX/EPUB/PDF
- `scripts/calibre_html_publish.py` — Calibre format conversion wrapper
- `scripts/template.html`, `scripts/template_ebook.html` — HTML templates
- `scripts/scholarly_dispatch.py` — Conservative router for scholarly Korean→English mode
- `scripts/scholarly_handoff.py` — hashed Codex→Claude scholarly handoff contract
- `scripts/reviewer_gate.py` — reviewer completion gate
- `SCHOLARLY_TRANSLATION.md`, `PHASE1_SKILL_ADDENDUM.md`, `PHASE2_SKILL_ADDENDUM.md`, `PHASE2_2_HANDOFF.md` — scholarly orchestration
- `.claude/commands/scholarly-translate.md` — standalone scholarly KO→EN command
- `.claude/commands/scholarly-review.md` — Phase 2.2 Codex-draft review command

## Testing changes

Test with a small PDF to verify the full pipeline:

```bash
python3 scripts/convert.py /path/to/small.pdf --olang zh
# then run translation via the skill
python3 scripts/merge_and_build.py --temp-dir <name>_temp --title "test"
```

Verify: all output_chunk*.md files exist, manifest validation passes, output formats generate.

## Conventions

- Only `chunk*.md` naming — no `page*` legacy support
- Pipeline output artifacts use the canonical names `book.html`, `book_doc.html`, `book.docx`, `book.epub`, `book.pdf`. Internal scripts and skip/cache logic depend on these names; if title-based filenames are added later they must be optional aliases/copies, not silent replacements
- SKILL.md frontmatter must stay single-line per field (OpenClaw parser requirement)
- Script paths in SKILL.md use `{baseDir}` not hardcoded paths
- Subagent instructions in SKILL.md must be platform-neutral (work on Claude Code, OpenClaw, Codex)
- README changes must be synced to both README.md and README.zh-CN.md
- Releases follow `.claude/commands/release.md` — three commands in order: `git push origin main`, `git tag vX.Y.Z && git push --tags`, `npx clawhub@latest publish ./ --version X.Y.Z`. Do not skip the git tag; it's the only version anchor in the repo

## Do not

- Do not reintroduce `page*` file support — it was intentionally removed
- Do not hardcode `~/.claude/skills/` paths in SKILL.md — use `{baseDir}`
- Do not put platform-specific tool names (Agent, sessions_spawn) in `allowed-tools` as the only option — keep the whitelist cross-platform
- Do not add mtime-based incremental rebuild for HTML/format generation — the current skip logic is intentionally simple (existence check). Metadata/template changes require manual cleanup. This is documented in the README.
