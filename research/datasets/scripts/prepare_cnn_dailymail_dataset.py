"""
TransformAI Research: CNN/DailyMail Dataset Preparation Pipeline
================================================================
Prepares a deterministic, stratified 60-document research evaluation corpus
from the official CNN/DailyMail benchmark (abisee/cnn_dailymail v3.0.0 test split)
for evaluating hypotheses H1, H2, and H3.

Integrity Rules:
- Deterministic sampling with seed=42
- Exactly 20 SHORT (<400 words), 20 MEDIUM (400-800 words), 20 LONG (>800 words)
- Human ground-truth integrity: facts initialized with status='UNANNOTATED' and facts=[]
- Output manifest is strictly real research (is_development_fixture=False)
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any

import pandas as pd
from huggingface_hub import hf_hub_download


REPO_ID = "abisee/cnn_dailymail"
SUBFOLDER = "3.0.0"
FILENAME = "test-00000-of-00001.parquet"

OUTPUT_DIR = Path("research/datasets/real_research")
DOCS_DIR = OUTPUT_DIR / "source_documents"
ANNOTATIONS_DIR = OUTPUT_DIR / "annotations"
CANDIDATES_DIR = OUTPUT_DIR / "candidates"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"


def clean_article_text(raw_text: str) -> str:
    """
    Clean boilerplate wire headers while preserving full substantive content.
    """
    text = raw_text.strip()
    
    # Common wire boilerplate prefixes
    wire_patterns = [
        r"^\(CNN\)\s*(--\s*)?",
        r"^[A-Z\s,]+(?:\(CNN\))\s*(--\s*)?",
        r"^[A-Z\s,]+--\s*",
        r"^\(Daily Mail\)\s*(--\s*)?",
        r"^PUBLISHED:\s*.*?\n",
        r"^UPDATED:\s*.*?\n",
    ]
    for pattern in wire_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    
    # Normalize multiple line breaks to standard double newline
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count_words(text: str) -> int:
    return len(text.split())


def derive_title(text: str, highlights: str) -> str:
    """Derive a clean, descriptive title from highlights or first sentence."""
    if highlights and len(highlights.strip()) > 0:
        first_bullet = highlights.strip().split("\n")[0].lstrip("-•* ").strip()
        if len(first_bullet) > 10:
            return first_bullet[:100]
    
    first_line = text.split("\n")[0].strip()
    first_sentence = re.split(r"[.!?]", first_line)[0].strip()
    if len(first_sentence) > 10:
        return first_sentence[:100]
    return first_line[:100]


def prepare_dataset(
    seed: int = 42,
    target_short: int = 20,
    target_medium: int = 20,
    target_long: int = 20,
    generate_candidate_workspaces: bool = False,
) -> Dict[str, Any]:
    print("=" * 70)
    print("TransformAI Research: Preparing CNN/DailyMail Research Dataset (M9A)")
    print("=" * 70)
    print(f"Dataset Repository: {REPO_ID} (version {SUBFOLDER})")
    print(f"Target split: test ({FILENAME})")
    print(f"Stratification: {target_short} SHORT, {target_medium} MEDIUM, {target_long} LONG (Seed: {seed})")

    # 1. Download/load parquet
    print("\n[Step 1/5] Downloading / Loading cached parquet from Hugging Face Hub...")
    file_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=f"{SUBFOLDER}/{FILENAME}",
        repo_type="dataset",
    )
    print(f"Loaded parquet file from: {file_path}")

    df = pd.read_parquet(file_path)
    total_candidates = len(df)
    print(f"Total candidate articles in test split: {total_candidates}")

    # 2. Filter & categorize
    print("\n[Step 2/5] Filtering and categorizing articles into length buckets...")
    valid_rows = []
    for idx, row in df.iterrows():
        raw_article = str(row.get("article", "")).strip()
        highlights = str(row.get("highlights", "")).strip()
        article_id = str(row.get("id", f"row_{idx}")).strip()

        if not raw_article or len(raw_article) < 50:
            continue

        cleaned = clean_article_text(raw_article)
        wc = count_words(cleaned)
        
        if wc < 400:
            category = "SHORT"
        elif wc <= 800:
            category = "MEDIUM"
        else:
            category = "LONG"

        valid_rows.append({
            "id": article_id,
            "raw_text": raw_article,
            "cleaned_text": cleaned,
            "highlights": highlights,
            "word_count": wc,
            "category": category,
        })

    candidates_df = pd.DataFrame(valid_rows)
    bucket_counts = candidates_df["category"].value_counts().to_dict()

    short_count = bucket_counts.get("SHORT", 0)
    med_count = bucket_counts.get("MEDIUM", 0)
    long_count = bucket_counts.get("LONG", 0)

    print(f"Eligible article counts by bucket:")
    print(f"  - SHORT  (< 400 words) : {short_count} articles")
    print(f"  - MEDIUM (400-800 w)   : {med_count} articles")
    print(f"  - LONG   (> 800 words) : {long_count} articles")

    # Verification: check enough candidates exist
    if short_count < target_short:
        raise ValueError(f"Insufficient SHORT candidates: {short_count} < {target_short}")
    if med_count < target_medium:
        raise ValueError(f"Insufficient MEDIUM candidates: {med_count} < {target_medium}")
    if long_count < target_long:
        raise ValueError(f"Insufficient LONG candidates: {long_count} < {target_long}")

    # 3. Stratified Deterministic Sampling
    print(f"\n[Step 3/5] Sampling deterministically with seed={seed}...")
    short_sample = candidates_df[candidates_df["category"] == "SHORT"].sample(n=target_short, random_state=seed)
    med_sample = candidates_df[candidates_df["category"] == "MEDIUM"].sample(n=target_medium, random_state=seed)
    long_sample = candidates_df[candidates_df["category"] == "LONG"].sample(n=target_long, random_state=seed)

    selected_dfs = [short_sample, med_sample, long_sample]
    combined_selected = pd.concat(selected_dfs, ignore_index=True)

    print(f"Successfully selected {len(combined_selected)} total documents.")

    # 4. Prepare Output Directories and Files
    print("\n[Step 4/5] Writing source documents and annotation workspaces...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    if generate_candidate_workspaces:
        CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

    manifest_docs = []
    doc_counter = 1

    for _, row in combined_selected.iterrows():
        doc_id = f"DOC-REAL-{doc_counter:03d}"
        cleaned_text = row["cleaned_text"]
        title = derive_title(cleaned_text, row["highlights"])
        sha256_hash = compute_sha256(cleaned_text)
        wc = row["word_count"]
        paragraphs = [p for p in cleaned_text.split("\n\n") if p.strip()]
        sec_count = max(1, len(paragraphs))
        category = row["category"]

        # Write clean source document
        doc_file_path = DOCS_DIR / f"{doc_id}.txt"
        with open(doc_file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        # Write Ground Truth Annotation Template (UNANNOTATED)
        annotation_file_path = ANNOTATIONS_DIR / f"{doc_id}.facts.json"
        annotation_payload = {
            "document_id": doc_id,
            "title": title,
            "source_hash_sha256": sha256_hash,
            "source_modality": "TXT",
            "word_count": wc,
            "section_count": sec_count,
            "annotation_status": "UNANNOTATED",
            "facts": [],
            "metadata": {
                "source_dataset": REPO_ID,
                "dataset_version": SUBFOLDER,
                "split": "test",
                "hf_article_id": row["id"],
                "length_category": category,
                "reference_highlights": row["highlights"],
            },
        }
        with open(annotation_file_path, "w", encoding="utf-8") as f:
            json.dump(annotation_payload, f, indent=2)

        # Write optional candidate suggestions workspace if requested
        if generate_candidate_workspaces:
            cand_file_path = CANDIDATES_DIR / f"{doc_id}.candidates.json"
            cand_payload = {
                "document_id": doc_id,
                "status": "CANDIDATE",
                "notice": "These are unreviewed candidate proposals. NEVER treat as research ground truth.",
                "candidate_facts": [],
            }
            with open(cand_file_path, "w", encoding="utf-8") as f:
                json.dump(cand_payload, f, indent=2)

        manifest_docs.append({
            "document_id": doc_id,
            "title": title,
            "file_path": f"source_documents/{doc_id}.txt",
            "source_hash_sha256": sha256_hash,
            "source_modality": "TXT",
            "length_category": category,
            "word_count": wc,
            "section_count": sec_count,
            "total_facts": 0,
            "annotation_status": "UNANNOTATED",
        })

        doc_counter += 1

    # 5. Write Manifest
    print("\n[Step 5/5] Generating real research dataset manifest...")
    manifest_payload = {
        "dataset_version": "real-benchmark-1.0.0",
        "dataset_name": "TransformAI Real-World Research Evaluation Benchmark",
        "is_development_fixture": False,
        "fixture_disclaimer": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "annotation_version": "1.0.0",
        "annotation_status": "UNANNOTATED",
        "total_documents": len(manifest_docs),
        "sampling_metadata": {
            "source_dataset": REPO_ID,
            "source_split": "test",
            "random_seed": seed,
            "stratification": {
                "SHORT": {"target": target_short, "eligible_candidates": short_count, "selected": target_short},
                "MEDIUM": {"target": target_medium, "eligible_candidates": med_count, "selected": target_medium},
                "LONG": {"target": target_long, "eligible_candidates": long_count, "selected": target_long},
            },
        },
        "documents": manifest_docs,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    print(f"Manifest successfully written to: {MANIFEST_PATH}")
    print("\nSummary:")
    print(f"  Total Documents Prepared: {len(manifest_docs)}")
    print(f"  Short (<400w): {target_short}")
    print(f"  Medium (400-800w): {target_medium}")
    print(f"  Long (>800w): {target_long}")
    print("  Status: Dataset preparation complete; ground-truth annotation pending.")
    print("=" * 70)

    return {
        "total_documents": len(manifest_docs),
        "short_count": target_short,
        "medium_count": target_medium,
        "long_count": target_long,
        "manifest_path": str(MANIFEST_PATH),
        "status": "Dataset preparation complete; ground-truth annotation pending.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare CNN/DailyMail research dataset for TransformAI M9")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stratified sampling (default: 42)")
    parser.add_argument("--generate-candidates", action="store_true", help="Generate candidate workspaces separately")
    args = parser.parse_args()

    prepare_dataset(seed=args.seed, generate_candidate_workspaces=args.generate_candidates)
