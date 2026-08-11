#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from pathlib import Path
VALID_MODALITY={"asserted","proposed","suggested","hypothesized","conditional","negative"}; VALID_POLARITY={"positive","negative"}
def _canonical(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def stable_hash(o): return hashlib.sha256(_canonical(o).encode()).hexdigest()
def validate_concepts(data):
    if data.get("version")!=1 or not isinstance(data.get("concepts"),list): raise ValueError("invalid author_concepts contract")
    ids=set()
    for i,c in enumerate(data["concepts"]):
        for k in ("id","term","definition_ko"):
            if not isinstance(c.get(k),str) or not c[k].strip(): raise ValueError(f"concept #{i}: invalid {k}")
        if c["id"] in ids: raise ValueError(f"duplicate concept id: {c['id']}")
        ids.add(c["id"])
    return data
def validate_claims(data,concept_ids=None):
    if data.get("version")!=1 or not isinstance(data.get("claims"),list): raise ValueError("invalid claims contract")
    ids=set()
    for i,c in enumerate(data["claims"]):
        for k in ("id","source_ko"):
            if not isinstance(c.get(k),str) or not c[k].strip(): raise ValueError(f"claim #{i}: invalid {k}")
        if c["id"] in ids: raise ValueError(f"duplicate claim id: {c['id']}")
        ids.add(c["id"])
        if c.get("modality","asserted") not in VALID_MODALITY: raise ValueError("invalid modality")
        if c.get("polarity","positive") not in VALID_POLARITY: raise ValueError("invalid polarity")
        if concept_ids is not None:
            missing=sorted(set(c.get("concept_ids",[]) or [])-concept_ids)
            if missing: raise ValueError(f"claim {c['id']}: unknown concept ids {missing}")
    return data
def load_concepts(path): return validate_concepts(json.loads(Path(path).read_text(encoding="utf-8")))
def load_claims(path,concepts=None): return validate_claims(json.loads(Path(path).read_text(encoding="utf-8")),{c["id"] for c in concepts.get("concepts",[])} if concepts else None)
def concept_context_for_text(data,text): return [c for c in data.get("concepts",[]) if any(s and s in text for s in [c.get("term",""),*(c.get("related_terms",[]) or [])])]
