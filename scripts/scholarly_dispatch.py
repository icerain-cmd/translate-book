#!/usr/bin/env python3
from __future__ import annotations
import argparse, json

ACADEMIC_CUES = {
    'academic','scholarly','paper','article','journal','thesis','dissertation',
    '학술','논문','학술지','투고','저널','학위논문'
}

def normalize_lang(value: str | None) -> str:
    if not value:
        return ''
    v=value.strip().lower()
    aliases={'korean':'ko','한국어':'ko','ko-kr':'ko','english':'en','영어':'en','en-us':'en','en-gb':'en'}
    return aliases.get(v,v)

def decide(source_lang: str | None, target_lang: str | None, mode: str | None, request: str='') -> dict:
    src=normalize_lang(source_lang); tgt=normalize_lang(target_lang)
    mode_n=(mode or '').strip().lower()
    req=(request or '').lower()
    explicit = mode_n in {'academic','scholarly','scholarly_ko_en','ko-en-humanities'}
    cue = any(cue in req for cue in ACADEMIC_CUES)
    scholarly = (src=='ko' and tgt=='en' and (explicit or cue))
    return {
        'source_lang':src,'target_lang':tgt,
        'requested_mode':mode_n or 'general',
        'scholarly_ko_en':scholarly,
        'route':'scholarly-ko-en' if scholarly else 'general',
        'profile':'profiles/ko-en-humanities.json' if scholarly else None,
        'rules':['PHASE1_SKILL_ADDENDUM.md','PHASE2_SKILL_ADDENDUM.md','SCHOLARLY_TRANSLATION.md'] if scholarly else ['SKILL.md'],
    }

def main():
    p=argparse.ArgumentParser(description='Conservative dispatcher for scholarly Korean-to-English translation.')
    p.add_argument('--source-lang', default='')
    p.add_argument('--target-lang', default='')
    p.add_argument('--mode', default='')
    p.add_argument('--request', default='')
    args=p.parse_args()
    print(json.dumps(decide(args.source_lang,args.target_lang,args.mode,args.request),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
