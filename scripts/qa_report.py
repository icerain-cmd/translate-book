#!/usr/bin/env python3
"""Aggregate scholarly-translation QA results into JSON and Markdown."""
from __future__ import annotations
import argparse, json
from pathlib import Path

AXES=("citation_integrity","locked_terminology","epistemic_strength","semantic_fidelity","concept_preservation","claim_preservation","negation_preservation","condition_preservation","relation_preservation")


def aggregate(parts: dict) -> dict:
    axes={}
    for axis in AXES:
        item=parts.get(axis,{"status":"not_run"})
        axes[axis]=item.get("status","not_run") if isinstance(item,dict) else str(item)
    blocking=any(v in {"fail","not_run"} for v in axes.values())
    blocking_axes=[k for k,v in axes.items() if v in {"fail","not_run"}]
    warnings=sum(1 for v in axes.values() if v=="warning")
    return {"schema_version":2,"publishable":not blocking,"axes":axes,"blocking_axes":blocking_axes,"warning_axes":warnings,"details":parts}


def markdown(report: dict) -> str:
    mark={"pass":"PASS","warning":"WARNING","fail":"FAIL","not_run":"NOT RUN"}
    lines=["# Translation Audit","",f"**Publishable:** {'YES' if report['publishable'] else 'NO'}","","| Axis | Result |","|---|---|"]
    for k,v in report["axes"].items(): lines.append(f"| {k.replace('_',' ').title()} | {mark.get(v,v.upper())} |")
    lines += ["","> FAIL and NOT RUN are blocking. WARNING requires scholarly review but does not automatically block publishing.",""]
    return "\n".join(lines)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("parts_json"); ap.add_argument("--json-out",required=True); ap.add_argument("--md-out",required=True)
    a=ap.parse_args(); parts=json.loads(Path(a.parts_json).read_text(encoding="utf-8")); r=aggregate(parts)
    Path(a.json_out).write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    Path(a.md_out).write_text(markdown(r),encoding="utf-8")
if __name__=="__main__": main()
