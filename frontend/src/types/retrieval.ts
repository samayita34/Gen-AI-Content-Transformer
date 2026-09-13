export interface RetrievalChunkItem {
  chunk_id: string;
  document_id: string;
  content: string;
  similarity_score: number; // 0.0 to 1.0 (higher = greater semantic similarity)
  page_number: number | null;
  section_title: string | null;
  chunk_index: number;
  chunking_strategy: string;
  source_filename: string;
  metadata: Record<string, unknown>;
}

export interface RetrievalSearchRequest {
  query: string;
  document_id?: string | null;
  top_k?: number;
  similarity_threshold?: number;
}

export interface RetrievalSearchResponse {
  query: string;
  results: RetrievalChunkItem[];
  total_retrieved: number;
}

export interface SourceReference {
  document_id: string;
  source_filename: string;
  chunk_id: string;
  chunk_index: number;
  page_number: number | null;
  section_title: string | null;
}

export interface NormalizedFact {
  fact_text: string;
  source_reference: SourceReference;
}

export interface NormalizedEntity {
  entity_name: string;
  entity_type: string;
  source_references: SourceReference[];
}

export interface NormalizedClaim {
  statement: string;
  source_reference: SourceReference;
}

export interface SourceDocumentSummary {
  document_id: string;
  source_filename: string;
  retrieved_chunk_count: number;
  pages: number[];
  sections: string[];
}

export interface NormalizedContextResponse {
  query: string;
  source_documents: SourceDocumentSummary[];
  retrieved_chunks: RetrievalChunkItem[];
  facts: NormalizedFact[];
  key_points: string[];
  entities: NormalizedEntity[];
  claims: NormalizedClaim[];
  source_references: SourceReference[];
}
