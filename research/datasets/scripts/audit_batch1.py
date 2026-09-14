import json
from pathlib import Path

docs = ['DOC-REAL-001', 'DOC-REAL-002', 'DOC-REAL-003', 'DOC-REAL-004', 'DOC-REAL-005']
annotations_dir = Path('research/datasets/real_research/annotations')
sources_dir = Path('research/datasets/real_research/source_documents')

total_facts = 0
type_dist = {}
imp_dist = {}
span_errors = []
multi_span_count = 0
facts_per_doc = {}
doc_summaries = []

for doc_id in docs:
    fact_file = annotations_dir / f'{doc_id}.facts.json'
    source_file = sources_dir / f'{doc_id}.txt'
    with open(fact_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(source_file, 'r', encoding='utf-8') as f:
        source_text = f.read()
        
    facts = data.get('facts', [])
    facts_per_doc[doc_id] = len(facts)
    total_facts += len(facts)
    
    doc_info = {
        "doc_id": doc_id,
        "title": data.get("title"),
        "status": data.get("annotation_status"),
        "fact_count": len(facts),
        "facts": []
    }
    
    for fact in facts:
        fid = fact['fact_id']
        statement = fact['statement']
        norm_stmt = fact.get('normalized_statement', '')
        ftype = fact['fact_type']
        imp = fact['importance']
        refs = fact.get('source_references', [])
        
        type_dist[ftype] = type_dist.get(ftype, 0) + 1
        imp_dist[imp] = imp_dist.get(imp, 0) + 1
        if len(refs) > 1:
            multi_span_count += 1
            
        ref_checks = []
        for ref in refs:
            s_char = ref['start_char']
            e_char = ref['end_char']
            expected = ref['verbatim_text_span']
            actual = source_text[s_char:e_char]
            match = (actual == expected)
            if not match:
                span_errors.append((doc_id, fid, s_char, e_char, expected, actual))
            ref_checks.append({
                "para_idx": ref.get("paragraph_idx"),
                "start_char": s_char,
                "end_char": e_char,
                "verbatim": expected,
                "match": match
            })
            
        doc_info["facts"].append({
            "fact_id": fid,
            "statement": statement,
            "type": ftype,
            "importance": imp,
            "span_count": len(refs),
            "references": ref_checks
        })
    doc_summaries.append(doc_info)

report = {
    "total_documents": len(docs),
    "total_facts": total_facts,
    "facts_per_doc": facts_per_doc,
    "type_distribution": type_dist,
    "importance_distribution": imp_dist,
    "multi_span_count": multi_span_count,
    "span_alignment_errors": len(span_errors),
    "documents": doc_summaries
}

with open('research/datasets/real_research/batch1_audit_summary.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)

print("AUDIT EXECUTION COMPLETE.")
print(f"Total Documents: {len(docs)}")
print(f"Total Facts: {total_facts}")
print(f"Facts Per Document: {facts_per_doc}")
print(f"Type Distribution: {type_dist}")
print(f"Importance Distribution: {imp_dist}")
print(f"Multi-Span Facts: {multi_span_count}")
print(f"Span Errors: {len(span_errors)}")
