#!/usr/bin/env python3
from __future__ import annotations
import re
from citation_guard import protect
HEADING_RE=re.compile(r"^(#{1,6})\s+(.+)$",re.M); HANGUL_RE=re.compile(r"[가-힣]")
def build(text):
    _,cmap=protect(text); headings=[{"level":len(m.group(1)),"text":m.group(2).strip()} for m in HEADING_RE.finditer(text)]
    return {"schema_version":2,"source_language":"ko" if len(HANGUL_RE.findall(text))>=10 else "unknown","target_language":"en","characters":len(text),"headings":headings,"protected_citation_count":len(cmap),"citation_tokens":list(cmap),"qa_required":["citation_integrity","locked_terminology","epistemic_strength","semantic_fidelity","concept_preservation","claim_preservation","negation_preservation","condition_preservation","relation_preservation"]}
