#!/usr/bin/env python3
from __future__ import annotations
import re
def count_surface(text,surface):
    if re.fullmatch(r"[A-Za-z0-9 _\-()]+",surface): return len(re.findall(r"(?<!\w)"+re.escape(surface)+r"(?!\w)",text))
    return text.count(surface)
def audit(source,target,terminology):
    issues=[]
    for t in terminology["terms"]:
        src_count=sum(count_surface(source,s) for s in [t["source"],*(t.get("aliases",[]) or [])])
        if not src_count: continue
        if t.get("status","preferred")=="locked" and count_surface(target,t["target"])==0: issues.append({"code":"LOCKED_TERM_MISSING","term_id":t["id"],"required":t["target"],"severity":"error"})
        forbidden={v:count_surface(target,v) for v in t.get("forbidden_variants",[]) or []}; forbidden={k:v for k,v in forbidden.items() if v}
        if forbidden: issues.append({"code":"FORBIDDEN_VARIANT_USED","term_id":t["id"],"variants":forbidden,"severity":"error"})
    return {"status":"fail" if issues else "pass","issues":issues}
