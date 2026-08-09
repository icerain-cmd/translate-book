#!/usr/bin/env python3
"""Deterministic preflight inventory for Korean-to-English scholarly translation."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from citation_guard import protect

HEADING_RE=re.compile(r"^(#{1,6})\s+(.+)$",re.M)
NUMBERED_HEADING_RE=re.compile(r"^\s*(\d+(?:\.\d+)*)(?:\.)?\s+([^\n]{2,120})$",re.M)
HANGUL_RE=re.compile(r"[가-힣]")


def build(text: str) -> dict:
    protected, cmap=protect(text)
    headings=[{"level":len(m.group(1)),"text":m.group(2).strip()} for m in HEADING_RE.finditer(text)]
    if not headings:
        for m in NUMBERED_HEADING_RE.finditer(text):
            depth=m.group(1).count(".")+1
            label=m.group(1)+( "." if depth==1 else "")
            headings.append({"level":depth,"text":f"{label} {m.group(2).strip()}","inferred":True})
    return {
        "schema_version":2,
        "source_language":"ko" if len(HANGUL_RE.findall(text))>=10 else "unknown",
        "target_language":"en",
        "characters":len(text),
        "headings":headings,
        "protected_citation_count":len(re.findall(r"⟦CIT_[0-9A-F]{12}⟧", protected)),
        "unique_protected_citations":len(set(cmap.values())),
        "citation_tokens":list(cmap.keys()),
        "qa_required":["citation_integrity","locked_terminology","epistemic_strength","semantic_fidelity","concept_preservation","claim_preservation","negation_preservation","condition_preservation","relation_preservation"]
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("--out",required=True)
    a=ap.parse_args(); data=build(Path(a.input).read_text(encoding="utf-8")); Path(a.out).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
