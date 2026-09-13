export type ProcessingStatus = "uploaded" | "processing" | "completed" | "failed";
export type ChunkingStrategy = "fixed_size" | "structure_aware";
export type SourceModality = "text" | "image" | "audio" | "video";

export interface DocumentUploadResponse {
  document_id: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  processing_status: ProcessingStatus;
  chunking_strategy: ChunkingStrategy;
  message: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  page_number?: number | null;
  section_title?: string | null;
  character_count: number;
  token_count: number;
  chunking_strategy: ChunkingStrategy;
  chunk_metadata: {
    modality?: SourceModality | string;
    timestamp_start_sec?: number | null;
    timestamp_end_sec?: number | null;
    formatted_timestamp?: string | null;
    avg_confidence?: number | null;
    element_types?: string[];
    [key: string]: unknown;
  };
  created_at: string;
}

export interface DocumentChunkListResponse {
  document_id: string;
  total_chunks: number;
  chunks: DocumentChunk[];
}

export interface DocumentDetail {
  id: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  processing_status: ProcessingStatus;
  page_count?: number | null;
  character_count?: number | null;
  word_count?: number | null;
  chunking_strategy: ChunkingStrategy;
  total_chunks: number;
  error_message?: string | null;
  doc_metadata: {
    modality?: SourceModality | string;
    duration_seconds?: number | null;
    media_metadata?: Record<string, unknown>;
    ocr_provider?: string;
    transcription_provider?: string;
    [key: string]: unknown;
  };
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentDetail[];
}
