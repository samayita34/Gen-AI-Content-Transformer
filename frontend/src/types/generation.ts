import { SourceReference } from "@/types/retrieval";

export type OutputType = "executive_summary" | "advisory" | "presentation" | "video_script";
export type AudienceType = "general_public" | "executive" | "technical" | "academic" | "operational";
export type ToneType = "neutral" | "professional" | "concise" | "formal" | "explanatory";
export type DetailLevel = "brief" | "moderate" | "detailed";
export type CommunicationObjective = "inform" | "brief" | "explain" | "persuade" | "prepare_action";

export interface TransformationRequest {
  document_id: string;
  output_type: OutputType;
  audience?: AudienceType;
  tone?: ToneType;
  detail_level?: DetailLevel;
  communication_objective?: CommunicationObjective;
  language?: string;
  length_constraint?: string | null;
  query?: string | null;
  custom_intent?: string | null;
  top_k?: number;
  similarity_threshold?: number;
}

export interface ExecutiveSummaryContent {
  title: string;
  overview: string;
  key_points: string[];
  important_facts: string[];
  implications: string[];
  conclusion: string;
  source_references?: SourceReference[];
}

export interface AdvisoryContent {
  title: string;
  situation: string;
  key_information: string[];
  risks_or_considerations: string[];
  recommended_actions: string[];
  important_notes: string[];
  conclusion: string;
  source_references?: SourceReference[];
}

export interface SlideItem {
  slide_number: number;
  title: string;
  bullets: string[];
  speaker_notes: string;
  source_references?: SourceReference[];
}

export interface PresentationContent {
  presentation_title: string;
  slides: SlideItem[];
}

export interface SceneItem {
  scene_number: number;
  visual_description: string;
  narration: string;
  on_screen_text: string;
  source_references?: SourceReference[];
}

export interface VideoScriptContent {
  title: string;
  target_duration: string;
  scenes: SceneItem[];
}

export interface TransformationResult {
  transformation_id: string;
  document_id: string;
  output_type: OutputType;
  configuration: Record<string, unknown>;
  content: ExecutiveSummaryContent | AdvisoryContent | PresentationContent | VideoScriptContent;
  source_references: SourceReference[];
  retrieved_chunk_ids: string[];
  retrieval_similarity_scores: number[];
  retrieval_ranks: number[];
  number_of_retrieved_chunks: number;
  provider: string;
  model: string;
  generation_latency_ms: number;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
  created_at: string;
}

export interface FormatOption {
  value: string;
  label: string;
  description: string;
}

export interface AvailableFormatsResponse {
  output_types: FormatOption[];
  audiences: FormatOption[];
  tones: FormatOption[];
  detail_levels: FormatOption[];
  objectives: FormatOption[];
}
