#!/usr/bin/env python3
from __future__ import annotations
AXES=("citation_integrity","locked_terminology","epistemic_strength","semantic_fidelity","concept_preservation","claim_preservation","negation_preservation","condition_preservation","relation_preservation")
def aggregate(parts):
    axes={}
    for axis in AXES:
        item=parts.get(axis,{"status":"not_run"}); axes[axis]=item.get("status","not_run") if isinstance(item,dict) else str(item)
    blocking=any(v=="fail" for v in axes.values()); warnings=sum(1 for v in axes.values() if v=="warning")
    return {"schema_version":2,"publishable":not blocking,"axes":axes,"warning_axes":warnings,"details":parts}
def markdown(report):
    mark={"pass":"PASS","warning":"WARNING","fail":"FAIL","not_run":"NOT RUN"}; lines=["# Translation Audit","",f"**Publishable:** {'YES' if report['publishable'] else 'NO'}","","| Axis | Result |","|---|---|"]
    for k,v in report["axes"].items(): lines.append(f"| {k.replace('_',' ').title()} | {mark.get(v,v.upper())} |")
    lines += ["","> A FAIL is blocking. WARNING requires scholarly review but does not automatically block publishing.",""]; return "\n".join(lines)
