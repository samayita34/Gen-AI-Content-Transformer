"""
TransformAI Research Experiment: Vector Retrieval Comparative Benchmark
========================================================================

SIH26154: Gen AI Platform for Automated Content Transformation
Milestone 3: RAG Retrieval + Context Normalization

Objective:
Empirically compare semantic vector retrieval behavior over:
- Method 1: Fixed-size chunked corpus (sliding-window baseline)
- Method 2: Structure-aware chunked corpus (heading/paragraph semantic boundaries)

Measures:
- Retrieval query latency (ms)
- Cosine similarity score distributions
- Provenance preservation (section titles, page numbers)
- Top-k chunk representation

Output:
Saves structured experiment results to `research/results/retrieval_comparison.json`.
"""

import json
import time
import math
import uuid
from pathlib import Path
from typing import List, Dict, Any

# Sample research test corpus
SAMPLE_CORPUS = """# 1. Executive Overview
The Next-Generation Content Transformation Platform addresses automated multimodal content synthesis.
Traditional workflows require significant human editorial effort to produce executive summaries, advisories,
and presentation decks. This project introduces a source-grounded RAG architecture with pgvector indexing.

# 2. System Architecture & Ingestion
Documents in PDF, DOCX, and TXT formats are ingested through a decoupled pipeline.
Deterministic cleaning removes control characters and normalizes Unicode without altering source facts.
Dense embeddings are generated using a 384-dimensional SentenceTransformer model (all-MiniLM-L6-v2).

# 3. Dense Vector Retrieval
Vector search calculates cosine similarity between the query embedding and indexed document chunks.
Cosine similarity is computed as 1 - cosine_distance, yielding a score between 0.0 and 1.0.
Every retrieved chunk maintains strict provenance, recording chunk index, page number, and section title.

# 4. Context Normalization & Grounding
Retrieved chunks are passed to a deterministic Context Builder.
Facts, key points, entities, and claims are mapped directly from source sentences.
Zero generative rewriting or hallucination occurs in the context normalization layer.
"""

BENCHMARK_QUERIES = [
    {
        "query_id": "Q1",
        "query": "What document formats are supported by the ingestion pipeline?",
        "target_topic": "System Architecture & Ingestion",
    },
    {
        "query_id": "Q2",
        "query": "How is vector cosine similarity calculated in pgvector?",
        "target_topic": "Dense Vector Retrieval",
    },
    {
        "query_id": "Q3",
        "query": "Does the context normalization layer rewrite source facts?",
        "target_topic": "Context Normalization & Grounding",
    },
    {
        "query_id": "Q4",
        "query": "What is the primary objective of the content transformation platform?",
        "target_topic": "Executive Overview",
    },
]


def _mock_dense_vector(text: str, dim: int = 384) -> List[float]:
    """Deterministic normalized vector simulation for reproducible offline experimentation."""
    import hashlib
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        return vec
    for word in words:
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        for i in range(4):
            idx = (h + i * 31) % dim
            vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm > 0 else vec


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    return max(0.0, min(1.0, float(dot)))


def run_experiment() -> Dict[str, Any]:
    print("=" * 70)
    print("TransformAI: Running Retrieval Comparative Experiment (Milestone 3)")
    print("=" * 70)

    # 1. Simulate Fixed-Size Chunking
    words = SAMPLE_CORPUS.split()
    chunk_size = 40
    fixed_chunks = []
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i : i + chunk_size]
        text = " ".join(chunk_words)
        fixed_chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "chunk_index": len(fixed_chunks),
            "content": text,
            "section_title": None,
            "page_number": 1,
            "strategy": "fixed_size",
            "embedding": _mock_dense_vector(text),
        })

    # 2. Simulate Structure-Aware Chunking (Heading boundaries)
    sections = SAMPLE_CORPUS.strip().split("\n\n")
    struct_chunks = []
    for s in sections:
        lines = s.strip().split("\n")
        title = lines[0].replace("#", "").strip() if lines[0].startswith("#") else "General"
        body = " ".join(lines[1:]) if lines[0].startswith("#") else s
        struct_chunks.append({
            "chunk_id": str(uuid.uuid4()),
            "chunk_index": len(struct_chunks),
            "content": body,
            "section_title": title,
            "page_number": 1,
            "strategy": "structure_aware",
            "embedding": _mock_dense_vector(s),
        })

    print(f"Generated {len(fixed_chunks)} Fixed-Size chunks and {len(struct_chunks)} Structure-Aware chunks.")

    results_data = {
        "metadata": {
            "experiment_name": "retrieval_chunking_comparison",
            "milestone": "Milestone 3",
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "embedding_dimension": 384,
            "top_k": 3,
            "similarity_metric": "cosine_similarity (1 - cosine_distance)",
        },
        "query_evaluations": [],
    }

    # 3. Evaluate each benchmark query
    for q_item in BENCHMARK_QUERIES:
        query_text = q_item["query"]
        q_vec = _mock_dense_vector(query_text)

        # Retrieve against Method 1 (Fixed)
        t0 = time.perf_counter()
        fixed_scored = []
        for ch in fixed_chunks:
            sim = _cosine_similarity(q_vec, ch["embedding"])
            fixed_scored.append((sim, ch))
        fixed_scored.sort(key=lambda x: x[0], reverse=True)
        t_fixed = (time.perf_counter() - t0) * 1000

        top_fixed = fixed_scored[:3]

        # Retrieve against Method 2 (Structure-Aware)
        t0 = time.perf_counter()
        struct_scored = []
        for ch in struct_chunks:
            sim = _cosine_similarity(q_vec, ch["embedding"])
            struct_scored.append((sim, ch))
        struct_scored.sort(key=lambda x: x[0], reverse=True)
        t_struct = (time.perf_counter() - t0) * 1000

        top_struct = struct_scored[:3]

        eval_entry = {
            "query_id": q_item["query_id"],
            "query": query_text,
            "target_topic": q_item["target_topic"],
            "method_1_fixed": {
                "strategy": "fixed_size",
                "retrieval_latency_ms": round(t_fixed, 3),
                "top_similarity_score": round(top_fixed[0][0], 4) if top_fixed else 0.0,
                "retrieved_chunks": [
                    {
                        "chunk_id": ch["chunk_id"],
                        "similarity": round(sim, 4),
                        "section_title": ch["section_title"],
                        "content_snippet": ch["content"][:100] + "...",
                    }
                    for sim, ch in top_fixed
                ],
            },
            "method_2_structure_aware": {
                "strategy": "structure_aware",
                "retrieval_latency_ms": round(t_struct, 3),
                "top_similarity_score": round(top_struct[0][0], 4) if top_struct else 0.0,
                "retrieved_chunks": [
                    {
                        "chunk_id": ch["chunk_id"],
                        "similarity": round(sim, 4),
                        "section_title": ch["section_title"],
                        "content_snippet": ch["content"][:100] + "...",
                    }
                    for sim, ch in top_struct
                ],
            },
        }
        results_data["query_evaluations"].append(eval_entry)

        print(f"\nQuery [{q_item['query_id']}]: '{query_text}'")
        print(f"  Fixed-Size Top Match (Score: {eval_entry['method_1_fixed']['top_similarity_score']}): Section={eval_entry['method_1_fixed']['retrieved_chunks'][0]['section_title']}")
        print(f"  Structure-Aware Top Match (Score: {eval_entry['method_2_structure_aware']['top_similarity_score']}): Section={eval_entry['method_2_structure_aware']['retrieved_chunks'][0]['section_title']}")

    # 4. Save results to research/results/
    out_dir = Path("research/results")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "retrieval_comparison.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"\n[OK] Experiment completed successfully. Results saved to '{out_path}'.")
    return results_data


if __name__ == "__main__":
    run_experiment()
