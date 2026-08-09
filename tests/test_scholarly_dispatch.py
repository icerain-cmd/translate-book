from scripts.scholarly_dispatch import decide


def test_explicit_scholarly_ko_en_routes():
    r = decide('ko', 'en', 'scholarly', '')
    assert r['scholarly_ko_en'] and r['route'] == 'scholarly-ko-en'


def test_korean_academic_cue_routes():
    r = decide('한국어', '영어', '', '이 논문을 학술 영어로 번역해')
    assert r['scholarly_ko_en']


def test_general_ko_en_does_not_route_without_academic_intent():
    r = decide('ko', 'en', 'general', 'translate this novel')
    assert not r['scholarly_ko_en']


def test_non_ko_source_never_routes():
    r = decide('ja', 'en', 'scholarly', 'academic paper')
    assert not r['scholarly_ko_en']
