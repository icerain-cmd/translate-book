import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'scripts'))
from theory_contract import validate_concepts,validate_claims,concept_context_for_text
from claim_audit import audit
from terminology import term_hash
from citation_guard import protect,restore

def test_citation_roundtrip():
    s='문장 (Kant, 2000) [12].'; p,m=protect(s); assert restore(p,m)==s

def test_term_hash_contract_changes():
    a={'source':'기계세','target':'Mechanocene','status':'locked'}; b=dict(a); b['forbidden_variants']=['Machinocene']; assert term_hash(a)!=term_hash(b)

def test_theory_contract_and_negation():
    concepts={'version':1,'concepts':[{'id':'we','term':'공진 주체','definition_ko':'분석 단위','related_terms':['WE']}]}; claims={'version':1,'claims':[{'id':'c1','source_ko':'WE는 주체가 아니라 분석 단위다.','concept_ids':['we'],'modality':'negative','polarity':'negative'}]}; validate_concepts(concepts); validate_claims(claims,{'we'}); assert concept_context_for_text(concepts,'공진 주체를 논한다.'); assert audit('WE는 책임 주체가 아니라 분석 단위다.','WE is the responsible subject and an analytical unit.')['status']=='fail'
