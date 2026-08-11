#!/usr/bin/env python3
from __future__ import annotations
import re
KO_NEG=[r"아니(?:다|라|며|고)",r"않(?:다|는다|으며)",r"없(?:다|으며|고)",r"불가능",r"금지"]; EN_NEG=[r"\bnot\b",r"\bno\b",r"\bnever\b",r"\bwithout\b",r"\bneither\b",r"\bcannot\b",r"\bdoes not\b",r"\bis not\b",r"\bare not\b"]
KO_COND=[r"경우",r"때에만",r"한에서",r"조건",r"라면",r"다면",r"때에는"]; EN_COND=[r"\bif\b",r"\bonly if\b",r"\bwhen\b",r"\bprovided that\b",r"\binsofar as\b",r"\bunder (?:the )?condition"]
KO_HEDGE=[r"볼\s+수\s+있다",r"가능성",r"제안한다",r"시사한다",r"추정",r"것으로\s+보인다"]; EN_HEDGE=[r"\bmay\b",r"\bmight\b",r"\bcan be\b",r"\bsuggests?\b",r"\bproposes?\b",r"\bappears?\b",r"\bseems?\b",r"\barguably\b"]
def anyp(ps,t,flags=0): return any(re.search(p,t,flags) for p in ps)
def audit(source_ko,target_en):
    issues=[]; sneg=anyp(KO_NEG,source_ko); tneg=anyp(EN_NEG,target_en,re.I); scond=anyp(KO_COND,source_ko); tcond=anyp(EN_COND,target_en,re.I); shedge=anyp(KO_HEDGE,source_ko); thedge=anyp(EN_HEDGE,target_en,re.I)
    if sneg and not tneg: issues.append({"code":"NEGATION_POSSIBLY_LOST","severity":"error"})
    if scond and not tcond: issues.append({"code":"CONDITION_POSSIBLY_LOST","severity":"warning"})
    if shedge and not thedge: issues.append({"code":"MODALITY_POSSIBLY_STRENGTHENED","severity":"warning"})
    status="fail" if any(i["severity"]=="error" for i in issues) else ("warning" if issues else "pass")
    return {"status":status,"issues":issues,"features":{"source_negation":sneg,"target_negation":tneg,"source_conditional":scond,"target_conditional":tcond,"source_hedge":shedge,"target_hedge":thedge}}
