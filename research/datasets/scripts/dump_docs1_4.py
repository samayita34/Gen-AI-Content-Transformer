import json
from pathlib import Path

docs = ['DOC-REAL-001', 'DOC-REAL-002', 'DOC-REAL-003', 'DOC-REAL-004']

for d in docs:
    sf = Path(f'research/datasets/real_research/source_documents/{d}.txt')
    af = Path(f'research/datasets/real_research/annotations/{d}.facts.json')
    with open(sf, 'r', encoding='utf-8') as f:
        src = f.read()
    with open(af, 'r', encoding='utf-8') as f:
        ann = json.load(f)
    print(f"==================================================")
    print(f"DOCUMENT: {d}")
    print(f"SOURCE TEXT ({len(src)} chars):\n{src}\n")
    print(f"==================================================")
    for fact in ann['facts']:
        fid = fact['fact_id']
        stmt = fact['statement']
        ftype = fact['fact_type']
        imp = fact['importance']
        print(f"[{fid}] ({ftype}, {imp})")
        print(f"  Prop: {stmt}")
        for idx, r in enumerate(fact['source_references']):
            print(f"  Span [{r['start_char']}:{r['end_char']}]: \"{r['verbatim_text_span']}\"")
        print()
