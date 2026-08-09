#!/usr/bin/env python3
from __future__ import annotations
import json
SYSTEM="""You are a bilingual theory-preservation auditor for Korean scholarly prose translated into English. Do not stylistically edit. Preserve ontology, definitions, scope conditions, negations, distinctions, modality, and relations among claims. Flag translations that turn an analytical unit into an ontological subject, a conditional claim into an unconditional claim, a proposal into an established fact, or a distinction into an equivalence. Return JSON only."""
SCHEMA={"concept_preservation":"pass|warning|fail","claim_preservation":"pass|warning|fail","negation_preservation":"pass|warning|fail","condition_preservation":"pass|warning|fail","modality_preservation":"pass|warning|fail","relation_preservation":"pass|warning|fail","concept_drift":[],"claim_drift":[],"relation_reversals":[],"scope_changes":[],"requires_retranslation":False}
def make_prompt(source_ko,target_en,concepts,claims,structural_audit=None):
    payload={"author_concepts":concepts,"claims":claims,"structural_audit":structural_audit or {}}
    return SYSTEM+"\n\nREQUIRED JSON SHAPE:\n"+json.dumps(SCHEMA,ensure_ascii=False,indent=2)+"\n\nAUTHOR THEORY CONTRACT:\n"+json.dumps(payload,ensure_ascii=False,indent=2)+"\n\nSOURCE (KO):\n"+source_ko+"\n\nTRANSLATION (EN):\n"+target_en
