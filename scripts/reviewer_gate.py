#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from scholarly_handoff import sha256_file, validate

REQUIRED_OUTPUTS = ("final_en", "publication_audit", "review_changes")

def check(handoff_path, final_en=None, publication_audit=None, review_changes=None):
    hp = Path(handoff_path)
    data = json.loads(hp.read_text(encoding="utf-8"))
    hv = validate(data, verify_files=True, handoff_dir=hp.parent)
    errors = list(hv["errors"])
    outputs = {"final_en": final_en, "publication_audit": publication_audit, "review_changes": review_changes}
    for key in REQUIRED_OUTPUTS:
        p = outputs[key]
        if not p or not Path(p).is_file():
            errors.append(f"reviewer output missing: {key}")
    if final_en and Path(final_en).is_file():
        h = sha256_file(final_en)
        if h == data["source"]["sha256"]:
            errors.append("final_en equals Korean source")
    return {"valid": not errors, "errors": errors, "outputs": outputs}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("handoff")
    p.add_argument("--final-en", required=True)
    p.add_argument("--publication-audit", required=True)
    p.add_argument("--review-changes", required=True)
    a = p.parse_args()
    r = check(a.handoff, a.final_en, a.publication_audit, a.review_changes)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    raise SystemExit(0 if r["valid"] else 2)

if __name__ == "__main__":
    main()
