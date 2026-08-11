#!/usr/bin/env python3
from __future__ import annotations
import json
SYSTEM="""You are a bilingual scholarly translation verifier for Korean humanities and social-science prose. Compare source and translation. Do not rewrite. Audit only. The author's theoretical claims have priority over stylistic elegance. Treat locked terminology as immutable. Detect omission, addition, claim strengthening or weakening, concept drift, relation reversal, and citation corruption. Return JSON only."""
SCHEMA={"meaning_preservation":"pass|warning|fail","terminology":"pass|warning|fail","argument_preservation":"pass|warning|fail","epistemic_strength":"pass|warning|fail","citation_integrity":"pass|warning|fail","omissions":[],"additions":[],"concept_drift":[],"relation_reversals":[],"requires_retranslation":False}
def make_prompt(source_ko,target_en,term_table="",concept_context=""):
    return SYSTEM+"\n\nREQUIRED JSON SHAPE:\n"+json.dumps(SCHEMA,ensure_ascii=False,indent=2)+"\n\nLOCKED/PREFERRED TERMS:\n"+term_table+"\n\nAUTHOR CONCEPT CONTEXT:\n"+concept_context+"\n\nSOURCE (KO):\n"+source_ko+"\n\nTRANSLATION (EN):\n"+target_en
