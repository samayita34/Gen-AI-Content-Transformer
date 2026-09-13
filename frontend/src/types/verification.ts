export type VerificationVerdict =
  | "supported"
  | "contradicted"
  | "partially_supported"
  | "insufficient_evidence";

export type ClaimType = "factual" | "statistical" | "attributional" | "implication";

export interface AtomicClaim {
  claim_id: string;
  text: string;
  normalized_text: string;
  output_format: string;
  source_output_reference?: string | null;
  claim_type: ClaimType;
  extraction_confidence?: number | null;
  statement?: string;
  context_source_field?: string;
  normalized_statement?: string;
}

export interface EvidenceMatch {
  chunk_id: string;
  document_id: string;
  chunk_content: string;
  similarity_score: number;
  page_number?: number | null;
  section_title?: string | null;
  modality?: string | null;
  timestamp_start_sec?: number | null;
  timestamp_end_sec?: number | null;
  formatted_timestamp?: string | null;
  spatial_bounds?: Record<string, number> | null;
  relevance_snippet: string;
  text?: string;
  similarity?: number;
  source_reference?: string | null;
}

export interface ClaimVerificationResult {
  claim: AtomicClaim;
  verdict: VerificationVerdict;
  explanation: string;
  evidence: EvidenceMatch[];
  confidence?: number | null;
  claim_id?: string;
  text?: string;
  normalized_text?: string;
}

export interface VerificationReport {
  report_id?: string;
  generated_output_id?: string | null;
  document_id: string;
  output_type: string;
  format?: string;
  total_claims: number;
  supported_claims: number;
  contradicted_claims: number;
  partially_supported_claims: number;
  insufficient_evidence_claims: number;
  claim_results: ClaimVerificationResult[];
  claims?: ClaimVerificationResult[];
  summary: string;
  created_at: string;
}

export interface VerificationRequest {
  document_id: string;
  output_type: string;
  transformation_content: Record<string, unknown>;
  top_k?: number;
  similarity_threshold?: number;
}
