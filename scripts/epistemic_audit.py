#!/usr/bin/env python3
from __future__ import annotations
import re
KO_HEDGES=[r"볼\s+수\s+있다",r"가능성(?:이|을)",r"제안한다",r"시사한다",r"판단한다",r"추정한다",r"일\s+수\s+있다",r"것으로\s+보인다"]
EN_STRONG=[r"\bproves?\b",r"\bdemonstrates?\b",r"\bestablish(?:es|ed)?\b",r"\bconfirms?\b"]
def audit(source_ko,target_en):
    hedges=[p for p in KO_HEDGES if re.search(p,source_ko)]; strong=[p for p in EN_STRONG if re.search(p,target_en,re.I)]; warnings=[]
    if hedges and strong: warnings.append({"code":"POSSIBLE_EPISTEMIC_STRENGTHENING","source_hedge_patterns":hedges,"target_strong_patterns":strong,"severity":"warning"})
    return {"status":"warning" if warnings else "pass","warnings":warnings}
