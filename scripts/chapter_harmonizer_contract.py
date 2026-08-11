#!/usr/bin/env python3
from __future__ import annotations
import json
SYSTEM="""You are an academic English harmonizer. Improve cohesion, article use, transitions, and Korean-to-English calques across the chapter. Do not change locked terminology, definitions, claim modality, negation, scope conditions, examples, citations, or logical relations among claims. Do not merge theoretically distinct claims. If a stylistic improvement risks changing meaning, keep the existing wording."""
def make_prompt(chapter_en,terminology,concepts,claims):
    return SYSTEM+"\n\nIMMUTABLE CONTRACT:\n"+json.dumps({"terminology":terminology,"concepts":concepts,"claims":claims},ensure_ascii=False,indent=2)+"\n\nCHAPTER TRANSLATION:\n"+chapter_en
