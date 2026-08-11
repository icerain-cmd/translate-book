#!/usr/bin/env python3
"""Protect immutable scholarly citation-like spans before LLM translation.

The guard intentionally targets high-confidence patterns only. It avoids trying
to parse every citation style; uncertain prose stays visible to the translator.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

PATTERNS = [
    re.compile(r"https?://[^\s)>\]}]+"),
    re.compile(r"\bdoi:\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I),
    re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", re.I),
    # Latin-script author-year citations, e.g. (Kant, 1790) or (Smith & Jones, 2024, p. 10).
    re.compile(r"\((?:[A-Z][A-Za-z'’\-]+(?:\s+(?:&|and)\s+[A-Z][A-Za-z'’\-]+)?(?:\s+et\s+al\.)?),?\s+(?:19|20)\d{2}[a-z]?(?:,\s*p{1,2}\.\s*\d+(?:[-–]\d+)?)?\)"),
    # Korean-script author-year citations, e.g. (이용욱, 2026), including common multi-author separators.
    re.compile(r"\((?:[가-힣]{2,10})(?:\s*(?:·|ㆍ|,|및|와|과|&|and)\s*[가-힣]{2,10})*,?\s*(?:19|20)\d{2}[a-z]?(?:,\s*(?:p{1,2}\.\s*)?\d+(?:[-–]\d+)?)?\)"),
    # Numbered citation markers.
    re.compile(r"\[(?:\d+|\d+(?:\s*[-–,]\s*\d+)+)\]"),
    # Draft footnote placeholders must survive translation byte-for-byte.
    re.compile(r"\[각주(?::[^\]]+)?\]"),
]
TOKEN_RE = re.compile(r"⟦CIT_[0-9A-F]{12}⟧")


def protect(text: str):
    spans = []
    for pat in PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.end(), m.group(0)))
    spans.sort(key=lambda x: (x[0], -(x[1]-x[0])))
    accepted = []
    end = -1
    for s,e,val in spans:
        if s >= end:
            accepted.append((s,e,val)); end=e
    mapping = {}
    out=[]; pos=0
    for s,e,val in accepted:
        out.append(text[pos:s])
        # Position participates in the token so repeated identical citations get
        # distinct immutable markers. Strict restore can therefore detect loss
        # of a single repeated occurrence.
        token_seed = f"{s}:{e}:{val}"
        token = "⟦CIT_" + hashlib.sha256(token_seed.encode("utf-8")).hexdigest()[:12].upper() + "⟧"
        mapping[token] = val
        out.append(token); pos=e
    out.append(text[pos:])
    return "".join(out), mapping


def restore(text: str, mapping: dict, strict=True):
    unknown = sorted(set(TOKEN_RE.findall(text)) - set(mapping))
    missing = sorted(set(mapping) - set(TOKEN_RE.findall(text)))
    if strict and (unknown or missing):
        raise ValueError(f"citation token mismatch: unknown={unknown}, missing={missing}")
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text


def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("protect"); p.add_argument("input"); p.add_argument("output"); p.add_argument("map")
    r=sub.add_parser("restore"); r.add_argument("input"); r.add_argument("output"); r.add_argument("map")
    a=ap.parse_args()
    if a.cmd=="protect":
        src=Path(a.input).read_text(encoding="utf-8")
        protected,m=protect(src)
        Path(a.output).write_text(protected,encoding="utf-8")
        Path(a.map).write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")
    else:
        src=Path(a.input).read_text(encoding="utf-8")
        m=json.loads(Path(a.map).read_text(encoding="utf-8"))
        Path(a.output).write_text(restore(src,m),encoding="utf-8")
if __name__=="__main__": main()
