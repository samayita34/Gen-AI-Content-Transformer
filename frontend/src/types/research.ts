export interface MetricStats {
  n: number;
  mean: number;
  median: number;
  std: number;
  iqr: number;
}

export interface AblationDelta {
  metric_name: string;
  baseline_value: number;
  experimental_value: number;
  delta: number;
  percent_change?: number | null;
  direction_improved: boolean;
}

export interface AblationStep {
  step_name: string;
  baseline_method: string;
  experimental_method: string;
  deltas: AblationDelta[];
}

export interface HypothesisTest {
  metric_name: string;
  comparison_name: string;
  test_used: string;
  sample_size: number;
  test_statistic: number;
  p_value: number;
  effect_size_cohens_d: number;
  confidence_interval_95: [number, number];
  assumptions_satisfied: boolean;
  limitation_notes?: string | null;
}

export interface Track1GenerationQuality {
  descriptive_statistics: Record<string, MetricStats>;
  hypothesis_testing?: Record<string, HypothesisTest>;
  ablations?: AblationStep[];
}

export interface ClassMetric {
  verdict: string;
  support: number;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface Track2VerificationQuality {
  total_samples: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  per_class: Record<string, ClassMetric>;
  confusion_matrix: Record<string, Record<string, number>>;
  binary_accuracy: number;
  binary_f1: number;
  evaluation_notes?: string | null;
}

export interface Track3OperationalTelemetry {
  method_latencies_ms: Record<string, number>;
  method_d_notice?: string;
}

export interface BenchmarkMetadata {
  dataset_name: string;
  dataset_version: string;
  is_development_fixture: boolean;
  fixture_disclaimer?: string;
  total_runs: number;
  generated_at: string;
}

export interface M7EvaluationSummary {
  benchmark_metadata: BenchmarkMetadata;
  track_1_generation_quality: Track1GenerationQuality;
  track_2_verification_quality: Track2VerificationQuality;
  track_3_operational_telemetry: Track3OperationalTelemetry;
}

export interface ResearchSummaryResponse {
  is_available: boolean;
  is_development_fixture: boolean;
  fixture_disclaimer?: string | null;
  message?: string | null;
  summary?: M7EvaluationSummary | null;
}
