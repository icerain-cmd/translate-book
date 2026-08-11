#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
VALID_STATUS={"locked","preferred","flexible"}; SCHEMA_VERSION=3
def _canonical(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def term_hash(term):
    fields={"source":term.get("source",""),"target":term.get("target",""),"status":term.get("status","preferred"),"category":term.get("category",""),"aliases":sorted(term.get("aliases",[]) or []),"allowed_variants":sorted(term.get("allowed_variants",[]) or []),"forbidden_variants":sorted(term.get("forbidden_variants",[]) or []),"context_rules":term.get("context_rules",[]) or []}
    return hashlib.sha256(_canonical(fields).encode()).hexdigest()
def validate(data):
    if data.get("version")!=SCHEMA_VERSION: raise ValueError("terminology version must be 3")
    terms=data.get("terms");
    if not isinstance(terms,list): raise ValueError("terms must be a list")
    ids=set()
    for i,t in enumerate(terms):
        for k in ("id","source","target"):
            if not isinstance(t.get(k),str) or not t[k].strip(): raise ValueError(f"term #{i}: {k} must be non-empty")
        if t["id"] in ids: raise ValueError(f"duplicate term id: {t['id']}")
        ids.add(t["id"])
        if t.get("status","preferred") not in VALID_STATUS: raise ValueError(f"invalid status: {t.get('status')}")
    return data
def load(path): return validate(json.loads(Path(path).read_text(encoding="utf-8")))
def terms_for_text(data,text): return [t for t in data["terms"] if any(s in text for s in [t["source"],*(t.get("aliases",[]) or [])])]
def prompt_table(terms):
    if not terms: return ""
    lines=["| Source | Required English | Status | Notes |","|---|---|---|---|"]
    for t in terms: lines.append(f"| {t['source']} | {t['target']} | {t.get('status','preferred').upper()} | {t.get('notes','').replace('|','\\|')} |")
    return "\n".join(lines)
