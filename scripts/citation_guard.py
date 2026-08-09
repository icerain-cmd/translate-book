#!/usr/bin/env python3
from __future__ import annotations
import hashlib,re
PATTERNS=[re.compile(r"https?://[^\s)>\]}]+"),re.compile(r"\bdoi:\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+",re.I),re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b",re.I),re.compile(r"\((?:[A-Z][A-Za-z'’\-]+(?:\s+(?:&|and)\s+[A-Z][A-Za-z'’\-]+)?(?:\s+et\s+al\.)?),?\s+(?:19|20)\d{2}[a-z]?(?:,\s*p{1,2}\.\s*\d+(?:[-–]\d+)?)?\)"),re.compile(r"\[(?:\d+|\d+(?:\s*[-–,]\s*\d+)+)\]")]
TOKEN_RE=re.compile(r"⟦CIT_[0-9A-F]{12}⟧")
def protect(text):
    spans=[]
    for p in PATTERNS:
        spans.extend((m.start(),m.end(),m.group(0)) for m in p.finditer(text))
    spans.sort(key=lambda x:(x[0],-(x[1]-x[0]))); accepted=[]; end=-1
    for s,e,v in spans:
        if s>=end: accepted.append((s,e,v)); end=e
    out=[]; mapping={}; pos=0
    for s,e,v in accepted:
        out.append(text[pos:s]); token="⟦CIT_"+hashlib.sha256(v.encode()).hexdigest()[:12].upper()+"⟧"; mapping[token]=v; out.append(token); pos=e
    out.append(text[pos:]); return "".join(out),mapping
def restore(text,mapping,strict=True):
    unknown=sorted(set(TOKEN_RE.findall(text))-set(mapping)); missing=sorted(set(mapping)-set(TOKEN_RE.findall(text)))
    if strict and (unknown or missing): raise ValueError(f"citation token mismatch: unknown={unknown}, missing={missing}")
    for token,original in mapping.items(): text=text.replace(token,original)
    return text
