#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
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

def path_candidates(path: str | Path, handoff_dir: str | Path | None = None):
    s = str(path)
    seen = set()
    out = []
    def add(v):
        if not v:
            return
        key = str(v)
        if key not in seen:
            seen.add(key); out.append(Path(v))
    add(s)
    add(_windows_to_wsl(s))
    add(_wsl_to_windows(s))
    if handoff_dir:
        base = Path(handoff_dir)
        p = Path(s)
        if not p.is_absolute() and not re.match(r"^[A-Za-z]:[\\/]", s):
            add(base / p)
        # Cross-host fallback: same basename beside the handoff or one directory above.
        name = s.replace("\\", "/").rstrip("/").split("/")[-1]
        if name:
            add(base / name); add(base.parent / name)
    return out

def resolve_artifact(obj, handoff_dir=None):
    if not obj:
        return None
    paths = []
    if obj.get("relative_path"):
        paths.append(obj["relative_path"])
    if obj.get("path"):
        paths.append(obj["path"])
    paths.extend(obj.get("locators") or [])
    for raw in paths:
        for p in path_candidates(raw, handoff_dir):
            if p.exists() and p.is_file():
                return p
    return None

def artifact(path: str | Path | None, anchor: str | Path | None = None):
    if not path:
        return None
    p = Path(path)
    obj = {"path": str(p), "sha256": sha256_file(p) if p.exists() and p.is_file() else None}
    if anchor:
        try:
            obj["relative_path"] = str(p.resolve().relative_to(Path(anchor).resolve()))
        except (ValueError, OSError):
            obj["relative_path"] = None
    else:
        obj["relative_path"] = None
    locators = []
    for candidate in (_windows_to_wsl(str(p)), _wsl_to_windows(str(p))):
        if candidate and candidate != str(p):
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
        "path_policy": {"identity": "sha256", "relative_to": "handoff_anchor", "cross_host_locators": True},
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
    if data.get("schema_version") not in (1, SCHEMA_VERSION):
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
        if not obj.get("path") or not obj.get("sha256"):
            errors.append(f"{name} artifact missing path/hash")
            continue
        if verify_files:
            p = resolve_artifact(obj, handoff_dir)
            if not p:
                errors.append(f"{name} file missing/unresolved: {obj.get('path')}")
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
    lines = [
        "# Scholarly Translation HANDOFF", "",
        f"- Workflow: `{data['workflow']}`",
        f"- Producer: **{data['producer']['agent']} / translator**",
        f"- Reviewer: **{data['reviewer']['agent']} / publication editor**",
        f"- Source: `{data['source']['path']}`",
        f"- Source SHA-256: `{data['source']['sha256']}`",
        f"- Codex translation: `{data['translation']['path']}`",
        f"- Translation SHA-256: `{data['translation']['sha256']}`",
        f"- Fresh translation: `{p['fresh_translation']}`",
        f"- Translated chunks: `{', '.join(p['translated_chunks']) or 'none'}`",
        f"- Retranslated chunks: `{', '.join(p['retranslated_chunks']) or 'none'}`",
        f"- Reused chunks: `{', '.join(p['reused_chunks']) or 'none'}`",
        "", "## Portability", "",
        "Artifact identity is the SHA-256 hash. Paths are locators only; Windows `R:\\...` and WSL `/mnt/r/...` forms are resolved automatically when possible.",
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
