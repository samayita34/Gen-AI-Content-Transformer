import re
import uuid
from typing import List, Dict, Any, Set
from app.services.retrieval.models import (
    RetrievedChunk,
    SourceReference,
    NormalizedFact,
    NormalizedEntity,
    NormalizedClaim,
    NormalizedContext,
)

# Regular expressions for deterministic entity & pattern recognition
ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)*\b")
NUMERIC_METRIC_PATTERN = re.compile(r"\b\d+(?:\.\d+)?(?:\s*(?:%|ms|s|MB|GB|TB|dimensions|dim|tokens|words|pages|users|kg|km|m))\b", re.IGNORECASE)
PROPER_NOUN_PHRASE_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b")


def _split_into_sentences(text: str) -> List[str]:
    """Splits text into discrete, clean sentence units."""
    if not text:
        return []
    # Split by period/question/exclamation followed by space or newline
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    clean_sentences = []
    for s in raw_sentences:
        s_clean = s.strip()
        if len(s_clean) > 10:  # Ignore fragments
            clean_sentences.append(s_clean)
    return clean_sentences


class ContextNormalizer:
    """
    Service responsible for converting raw retrieved vector chunks into a standardized,
    100% source-grounded NormalizedContext object for downstream generation agents.
    
    Guarantees:
    - Zero generative hallucination or inference.
    - Deterministic entity, fact, and claim attribution.
    - Full provenance traceability to document_id, page_number, and chunk_index.
    """

    def build_normalized_context(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> NormalizedContext:
        """
        Builds a NormalizedContext object from a list of retrieved chunks.
        """
        if not retrieved_chunks:
            return NormalizedContext(
                query=query,
                source_documents=[],
                retrieved_chunks=[],
                facts=[],
                key_points=[],
                entities=[],
                claims=[],
                source_references=[],
            )

        # 1. Deduplication while preserving top rank order
        seen_chunk_ids: Set[uuid.UUID] = set()
        seen_contents: Set[str] = set()
        deduped_chunks: List[RetrievedChunk] = []

        for chunk in retrieved_chunks:
            # Normalize whitespace for content comparison
            normalized_content = " ".join(chunk.content.split())
            if chunk.chunk_id in seen_chunk_ids or normalized_content in seen_contents:
                continue
            seen_chunk_ids.add(chunk.chunk_id)
            seen_contents.add(normalized_content)
            deduped_chunks.append(chunk)

        # 2. Document Grouping & Source Documents Catalog
        doc_map: Dict[uuid.UUID, Dict[str, Any]] = {}
        for chunk in deduped_chunks:
            if chunk.document_id not in doc_map:
                doc_map[chunk.document_id] = {
                    "document_id": str(chunk.document_id),
                    "source_filename": chunk.source_filename,
                    "retrieved_chunk_count": 0,
                    "pages": set(),
                    "sections": set(),
                }
            doc_map[chunk.document_id]["retrieved_chunk_count"] += 1
            if chunk.page_number is not None:
                doc_map[chunk.document_id]["pages"].add(chunk.page_number)
            if chunk.section_title:
                doc_map[chunk.document_id]["sections"].add(chunk.section_title)

        source_documents = []
        for doc_id, data in doc_map.items():
            source_documents.append({
                "document_id": data["document_id"],
                "source_filename": data["source_filename"],
                "retrieved_chunk_count": data["retrieved_chunk_count"],
                "pages": sorted(list(data["pages"])),
                "sections": sorted(list(data["sections"])),
            })

        # 3. Source References, Facts, Key Points, Claims Extraction
        source_references: List[SourceReference] = []
        facts: List[NormalizedFact] = []
        key_points: List[str] = []
        claims: List[NormalizedClaim] = []
        entities_dict: Dict[str, Dict[str, Any]] = {}

        for chunk in deduped_chunks:
            chunk_meta = chunk.metadata or {}
            source_ref = SourceReference(
                document_id=chunk.document_id,
                source_filename=chunk.source_filename,
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                section_title=chunk.section_title,
                modality=chunk_meta.get("modality", "text"),
                formatted_timestamp=chunk_meta.get("formatted_timestamp"),
            )
            source_references.append(source_ref)

            # Key point (top-ranked representative snippet)
            if len(key_points) < 5:
                # Use first substantive sentence as key point
                sentences = _split_into_sentences(chunk.content)
                if sentences:
                    key_points.append(sentences[0])
                else:
                    key_points.append(chunk.content[:150].strip())

            # Deterministic Facts & Claims (Source sentences mapped to provenance)
            sentences = _split_into_sentences(chunk.content)
            for sentence in sentences:
                facts.append(NormalizedFact(fact_text=sentence, source_reference=source_ref))
                # For direct assertion claims, preserve statement with provenance
                if any(kw in sentence.lower() for kw in ["must", "should", "will", "is", "are", "causes", "provides", "achieves"]):
                    claims.append(NormalizedClaim(statement=sentence, source_reference=source_ref))

            # Deterministic Entity Extraction
            content_text = chunk.content

            # Acronyms
            for match in ACRONYM_PATTERN.finditer(content_text):
                ent = match.group(0)
                if len(ent) >= 2 and ent not in ["THE", "AND", "FOR", "WITH", "FROM"]:
                    if ent not in entities_dict:
                        entities_dict[ent] = {"type": "ACRONYM", "refs": []}
                    if source_ref not in entities_dict[ent]["refs"]:
                        entities_dict[ent]["refs"].append(source_ref)

            # Proper Noun Phrases
            for match in PROPER_NOUN_PHRASE_PATTERN.finditer(content_text):
                ent = match.group(0)
                if ent not in entities_dict:
                    entities_dict[ent] = {"type": "PROPER_NOUN", "refs": []}
                if source_ref not in entities_dict[ent]["refs"]:
                    entities_dict[ent]["refs"].append(source_ref)

            # Numeric Metrics
            for match in NUMERIC_METRIC_PATTERN.finditer(content_text):
                ent = match.group(0)
                if ent not in entities_dict:
                    entities_dict[ent] = {"type": "METRIC", "refs": []}
                if source_ref not in entities_dict[ent]["refs"]:
                    entities_dict[ent]["refs"].append(source_ref)

        entities: List[NormalizedEntity] = [
            NormalizedEntity(
                entity_name=ent_name,
                entity_type=data["type"],
                source_references=data["refs"],
            )
            for ent_name, data in sorted(entities_dict.items(), key=lambda x: x[0])
        ]

        return NormalizedContext(
            query=query,
            source_documents=source_documents,
            retrieved_chunks=deduped_chunks,
            facts=facts,
            key_points=key_points,
            entities=entities,
            claims=claims,
            source_references=source_references,
        )


# Global default context normalizer instance
default_context_normalizer = ContextNormalizer()
