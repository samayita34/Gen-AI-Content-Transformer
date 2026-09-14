import json
from pathlib import Path

# 1. Update DOC-REAL-001
with open('research/datasets/real_research/annotations/DOC-REAL-001.facts.json', 'r', encoding='utf-8') as f:
    doc1 = json.load(f)

for fact in doc1['facts']:
    if fact['fact_id'] == 'FACT-REAL01-001':
        fact['statement'] = "Police said an Indian software pioneer and nine others were sentenced to seven years in jail for their roles in what was described as India's biggest corporate scandal in memory."
        fact['normalized_statement'] = "Police said Indian software pioneer and nine others sentenced to seven years in jail for corporate scandal."
        fact['fact_type'] = "ATTRIBUTIONAL"
    elif fact['fact_id'] == 'FACT-REAL01-003':
        fact['statement'] = "A spokesman for India's Central Bureau of Investigation told CNN that Ramalinga Raju was fined $804,000."
        fact['normalized_statement'] = "CBI spokesman told CNN that Ramalinga Raju was fined $804,000."
        fact['fact_type'] = "ATTRIBUTIONAL"
    elif fact['fact_id'] == 'FACT-REAL01-007':
        fact['statement'] = "The Central Bureau of Investigation said a special court convicted Raju and nine other people of cheating, criminal conspiracy, breach of public trust and other charges."
        fact['normalized_statement'] = "CBI said special court convicted Raju and nine others of cheating, criminal conspiracy, breach of trust."
        fact['fact_type'] = "ATTRIBUTIONAL"

with open('research/datasets/real_research/annotations/DOC-REAL-001.facts.json', 'w', encoding='utf-8') as f:
    json.dump(doc1, f, indent=2, ensure_ascii=False)

# 2. Update DOC-REAL-002
with open('research/datasets/real_research/annotations/DOC-REAL-002.facts.json', 'r', encoding='utf-8') as f:
    doc2 = json.load(f)

with open('research/datasets/real_research/source_documents/DOC-REAL-002.txt', 'r', encoding='utf-8') as f:
    src2 = f.read()

for fact in doc2['facts']:
    if fact['fact_id'] == 'FACT-REAL02-001':
        # Add multi-span references [0:113] and [114:270]
        span1_text = src2[0:113]
        span2_text = src2[114:270]
        fact['source_references'] = [
            {
                "paragraph_idx": 0,
                "sentence_idx": 0,
                "start_char": 0,
                "end_char": 113,
                "verbatim_text_span": span1_text
            },
            {
                "paragraph_idx": 0,
                "sentence_idx": 1,
                "start_char": 114,
                "end_char": 270,
                "verbatim_text_span": span2_text
            }
        ]
        fact['source_reference'] = fact['source_references'][0]

with open('research/datasets/real_research/annotations/DOC-REAL-002.facts.json', 'w', encoding='utf-8') as f:
    json.dump(doc2, f, indent=2, ensure_ascii=False)

# 3. Update DOC-REAL-003
with open('research/datasets/real_research/annotations/DOC-REAL-003.facts.json', 'r', encoding='utf-8') as f:
    doc3 = json.load(f)

with open('research/datasets/real_research/source_documents/DOC-REAL-003.txt', 'r', encoding='utf-8') as f:
    src3 = f.read()

span1_text_3 = src3[0:143]
span2_text_3 = src3[144:324]

for fact in doc3['facts']:
    if fact['fact_id'] == 'FACT-REAL03-003':
        fact['source_references'] = [
            {
                "paragraph_idx": 0,
                "sentence_idx": 0,
                "start_char": 0,
                "end_char": 143,
                "verbatim_text_span": span1_text_3
            },
            {
                "paragraph_idx": 0,
                "sentence_idx": 1,
                "start_char": 144,
                "end_char": 324,
                "verbatim_text_span": span2_text_3
            }
        ]
        fact['source_reference'] = fact['source_references'][0]
    elif fact['fact_id'] == 'FACT-REAL03-004':
        fact['source_references'] = [
            {
                "paragraph_idx": 0,
                "sentence_idx": 0,
                "start_char": 0,
                "end_char": 143,
                "verbatim_text_span": span1_text_3
            },
            {
                "paragraph_idx": 0,
                "sentence_idx": 1,
                "start_char": 144,
                "end_char": 324,
                "verbatim_text_span": span2_text_3
            }
        ]
        fact['source_reference'] = fact['source_references'][0]

with open('research/datasets/real_research/annotations/DOC-REAL-003.facts.json', 'w', encoding='utf-8') as f:
    json.dump(doc3, f, indent=2, ensure_ascii=False)

# 4. Update DOC-REAL-005
with open('research/datasets/real_research/annotations/DOC-REAL-005.facts.json', 'r', encoding='utf-8') as f:
    doc5 = json.load(f)

for fact in doc5['facts']:
    if fact['fact_id'] == 'FACT-REAL05-013':
        fact['statement'] = "Lian Marshall stated that the Easter eggs were still arriving."
        fact['normalized_statement'] = "Lian Marshall stated Easter eggs still arriving."
        fact['fact_type'] = "ATTRIBUTIONAL"

with open('research/datasets/real_research/annotations/DOC-REAL-005.facts.json', 'w', encoding='utf-8') as f:
    json.dump(doc5, f, indent=2, ensure_ascii=False)

print("CORRECTIONS APPLIED TO 7 FACTS.")
