#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re
from pathlib import Path

SCHEMA_VERSION = 2
WORKFLOW = "codex-translator-to-claude-reviewer"
REQUIRED_DO_NOT_REVERSE = [
    "Do not retranslate the manuscript from scratch.",
    "Do not modify the Korean source.",
    "Do not modify Codex translator artifacts in place.",
    "Do not change LOCKED terminology without an explicit blocking error and a recorded reason.",
    "Do not strengthen or weaken theoretical claims, negations, conditions, or modality.",
]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _windows_to_wsl(s: str) -> str | None:
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", s)
    if not m:
        return None
    return "/mnt/" + m.group(1).lower() + "/" + m.group(2).replace("\\", "/")


def _wsl_to_windows(s: str) -> str | None:
    m = re.match(r"^/mnt/([A-Za-z])/(.*)$", s)
    if not m:
        return None
    return m.group(1).upper() + ":\\" + m.group(2).replace("/", "\\")


def _is_windows_absolute(s: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", s))


def _portable_relative_candidate(relative_path: str | Path, handoff_dir: str | Path | None):
    if not handoff_dir:
        return None
    s = str(relative_path).strip()
    if not s or s.startswith("/") or _is_windows_absolute(s):
        return None
    parts = [part for part in re.split(r"[\\/]+", s) if part not in ("", ".")]
    return Path(handoff_dir).joinpath(*parts)


def path_candidates(path: str | Path, handoff_dir: str | Path | None = None):
    s = str(path)
    seen = set()
    out = []

    def add(v):
        if not v:
            return
        p = Path(v)
        key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)

    if s.startswith("/") or Path(s).is_absolute() or _is_windows_absolute(s):
        add(s)
        add(_windows_to_wsl(s))
        add(_wsl_to_windows(s))
    else:
        # Relative locators are anchored to the handoff, never to the caller's CWD.
        rel = _portable_relative_candidate(s, handoff_dir)
        if rel is not None:
            add(rel)
        else:
            add(s)

    return out


def _existing_local_path(path: str | Path, *, allow_dir: bool = False):
    for p in path_candidates(path):
        if p.exists() and (p.is_file() or (allow_dir and p.is_dir())):
            return p
    return None


def _canonical_relative_path(path: Path, anchor: Path) -> str | None:
    try:
        rel = os.path.relpath(path.resolve(), anchor.resolve())
    except (ValueError, OSError):
        return None
    # POSIX separators keep the canonical relative path producer-OS independent.
    return rel.replace("\\", "/")


def _artifact_candidate_paths(obj, handoff_dir=None):
    seen = set()
    out = []

    def add(p):
        if p is None:
            return
        key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)

    if obj.get("relative_path"):
        add(_portable_relative_candidate(obj["relative_path"], handoff_dir))
    if obj.get("path"):
        for p in path_candidates(obj["path"], handoff_dir):
            add(p)
    for locator in obj.get("locators") or []:
        raw = locator.get("path") if isinstance(locator, dict) else locator
        if raw:
            for p in path_candidates(raw, handoff_dir):
                add(p)
    return out


def resolve_artifact(obj, handoff_dir=None):
    if not obj:
        return None
    expected = obj.get("sha256")
    existing = []
    for p in _artifact_candidate_paths(obj, handoff_dir):
        if p.exists() and p.is_file():
            if expected and sha256_file(p) == expected:
                return p.resolve()
            existing.append(p.resolve())
    # If nothing matches the expected hash, preserve an existing candidate so
    # validate() reports a hash mismatch instead of incorrectly reporting missing.
    return existing[0] if existing else None


def artifact(path: str | Path | None, anchor: str | Path | None = None):
    if not path:
        return None

    original = str(path)
    local = _existing_local_path(path)
    obj = {
        "path": original,  # producer/legacy locator only in schema v2
        "sha256": sha256_file(local) if local else None,
        "relative_path": None,
        "locators": [],
    }

    if anchor and local:
        local_anchor = _existing_local_path(anchor, allow_dir=True) or Path(anchor)
        obj["relative_path"] = _canonical_relative_path(local, local_anchor)

    locators = []
    for value in (original, str(local) if local else None):
        if not value:
            continue
        for candidate in (value, _windows_to_wsl(value), _wsl_to_windows(value)):
            if candidate and candidate != original and candidate not in locators:
                locators.append(candidate)
    obj["locators"] = locators
    return obj


def build(source, translation, *, temp_dir=None, translation_audit=None, terminology=None, concepts=None, claims=None,
          fresh_translation=False, translated_chunks=None, retranslated_chunks=None, reused_chunks=None, producer="codex", anchor=None):
    anchor = Path(anchor) if anchor else (Path(temp_dir).parent if temp_dir else Path(source).parent)
    return {
        "schema_version": SCHEMA_VERSION,
        "workflow": WORKFLOW,
        "producer": {"agent": producer, "role": "translator"},
        "reviewer": {"agent": "claude-code", "role": "reviewer-publication-editor"},
        "path_policy": {
            "identity": ["relative_path", "sha256"],
            "relative_path_format": "posix",
            "absolute_paths": "locators_only",
            "cross_host_locators": True,
        },
        "source": artifact(source, anchor),
        "translation": artifact(translation, anchor),
        "temp_dir": str(temp_dir) if temp_dir else None,
        "contracts": {
            "terminology": artifact(terminology, anchor),
            "author_concepts": artifact(concepts, anchor),
            "claims": artifact(claims, anchor),
        },
        "translation_audit": artifact(translation_audit, anchor),
        "provenance": {
            "fresh_translation": bool(fresh_translation),
            "translated_chunks": translated_chunks or [],
            "retranslated_chunks": retranslated_chunks or [],
            "reused_chunks": reused_chunks or [],
        },
        "review_policy": {
            "review_existing_translation_only": True,
            "allowed_change_types": [
                "semantic_correction", "academic_english", "terminology_consistency",
                "citation_localization", "bibliography_normalization", "front_matter_cleanup",
            ],
            "required_outputs": ["final_en", "publication_audit", "review_changes"],
            "do_not_reverse": list(REQUIRED_DO_NOT_REVERSE),
        },
    }


def validate(data, verify_files=True, handoff_dir=None):
    errors = []
    schema = data.get("schema_version")
    if schema not in (1, SCHEMA_VERSION):
        errors.append("unsupported schema_version")
    if data.get("workflow") != WORKFLOW:
        errors.append("wrong workflow")
    if data.get("producer", {}).get("role") != "translator":
        errors.append("producer role must be translator")
    if data.get("reviewer", {}).get("role") != "reviewer-publication-editor":
        errors.append("reviewer role mismatch")
    if not data.get("review_policy", {}).get("review_existing_translation_only"):
        errors.append("review must use existing translation")

    for name in ("source", "translation"):
        obj = data.get(name) or {}
        if not obj.get("sha256"):
            errors.append(f"{name} artifact missing hash")
            continue
        if schema == 1:
            if not obj.get("path"):
                errors.append(f"{name} artifact missing path")
                continue
        elif not obj.get("relative_path"):
            errors.append(f"{name} artifact missing canonical relative_path")
            continue

        if verify_files:
            p = resolve_artifact(obj, handoff_dir)
            if not p:
                errors.append(f"{name} file missing/unresolved: {obj.get('relative_path') or obj.get('path')}")
            elif sha256_file(p) != obj["sha256"]:
                errors.append(f"{name} hash mismatch")

    if data.get("source", {}).get("sha256") == data.get("translation", {}).get("sha256"):
        errors.append("source and translation hashes must differ")
    missing_rules = [r for r in REQUIRED_DO_NOT_REVERSE if r not in data.get("review_policy", {}).get("do_not_reverse", [])]
    if missing_rules:
        errors.append("required do_not_reverse rules missing")
    return {"valid": not errors, "errors": errors}


def markdown(data):
    p = data["provenance"]
    source_ref = data["source"].get("relative_path") or data["source"].get("path")
    translation_ref = data["translation"].get("relative_path") or data["translation"].get("path")
    lines = [
        "# Scholarly Translation HANDOFF", "",
        f"- Workflow: `{data['workflow']}`",
        f"- Producer: **{data['producer']['agent']} / translator**",
        f"- Reviewer: **{data['reviewer']['agent']} / publication editor**",
        f"- Source relative path: `{source_ref}`",
        f"- Source SHA-256: `{data['source']['sha256']}`",
        f"- Codex translation relative path: `{translation_ref}`",
        f"- Translation SHA-256: `{data['translation']['sha256']}`",
        f"- Fresh translation: `{p['fresh_translation']}`",
        f"- Translated chunks: `{', '.join(p['translated_chunks']) or 'none'}`",
        f"- Retranslated chunks: `{', '.join(p['retranslated_chunks']) or 'none'}`",
        f"- Reused chunks: `{', '.join(p['reused_chunks']) or 'none'}`",
        "", "## Portability", "",
        "Artifact identity is the canonical POSIX-style `relative_path` plus SHA-256. Absolute Windows/WSL paths are locators only. Common `R:\\...` and `/mnt/r/...` forms are resolved automatically when possible.",
        "", "## Claude Reviewer Contract", "",
        "Claude Code reviews the Codex translation. It does **not** independently translate the Korean manuscript from scratch.",
        "", "### Do not reverse",
    ]
    lines += [f"- {x}" for x in data["review_policy"]["do_not_reverse"]]
    lines += [
        "", "### Required reviewer outputs", "",
        "- `final-en.md` — reviewed publication candidate",
        "- `publication-audit.md` — publication-readiness gate",
        "- `review-changes.md` — auditable before/after changes with reasons",
        "", "The original source and Codex translator artifacts are immutable inputs to the reviewer.",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--source", required=True); c.add_argument("--translation", required=True); c.add_argument("--output", required=True)
    c.add_argument("--temp-dir"); c.add_argument("--translation-audit"); c.add_argument("--terminology"); c.add_argument("--concepts"); c.add_argument("--claims"); c.add_argument("--anchor")
    c.add_argument("--fresh-translation", action="store_true"); c.add_argument("--translated-chunk", action="append", default=[]); c.add_argument("--retranslated-chunk", action="append", default=[]); c.add_argument("--reused-chunk", action="append", default=[])
    v = sub.add_parser("validate"); v.add_argument("handoff"); v.add_argument("--no-file-check", action="store_true")
    args = ap.parse_args()
    if args.cmd == "create":
        out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
        d = build(args.source, args.translation, temp_dir=args.temp_dir, translation_audit=args.translation_audit, terminology=args.terminology, concepts=args.concepts, claims=args.claims, fresh_translation=args.fresh_translation, translated_chunks=args.translated_chunk, retranslated_chunks=args.retranslated_chunk, reused_chunks=args.reused_chunk, anchor=args.anchor or out.parent)
        out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        out.with_name("HANDOFF.md").write_text(markdown(d), encoding="utf-8")
        print(json.dumps(validate(d, handoff_dir=out.parent), ensure_ascii=False))
    else:
        hp = Path(args.handoff)
        d = json.loads(hp.read_text(encoding="utf-8"))
        r = validate(d, not args.no_file_check, handoff_dir=hp.parent)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        raise SystemExit(0 if r["valid"] else 2)


if __name__ == "__main__":
    main()
