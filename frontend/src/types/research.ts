export interface MetricStats {
  n: number;
  mean: number;
  median: number;
  std: number;
  iqr: number;
}

export interface AblationDelta {
  comparison: string;
  metric: string;
  mean_delta: number;
  relative_change_pct: number;
}

export interface StatisticalTest {
  method_1: string;
  method_2: string;
  t_statistic?: number | null;
  p_value?: number | null;
  cohens_d?: number | null;
  alpha: number;
  is_statistically_significant: boolean;
  sample_size: number;
  test_name: string;
  small_sample_warning: boolean;
}

export interface Track1GenerationQuality {
  descriptive_statistics: Record<string, MetricStats>;
  ablation_deltas: AblationDelta[];
  statistical_significance_tests: Record<string, StatisticalTest>;
}

export interface VerificationMetrics {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface Track2VerificationQuality {
  macro_f1: number;
  binary_grouping: {
    precision: number;
    recall: number;
    f1_score: number;
    support: number;
  };
  classification_report: Record<string, VerificationMetrics>;
  confusion_matrix: {
    labels: string[];
    matrix: number[][];
  };
}

export interface Track3OperationalLatency {
  latency_by_method: Record<string, MetricStats>;
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
  track_3_operational_latency: Track3OperationalLatency;
}

export interface ResearchSummaryResponse {
  is_available: boolean;
  is_development_fixture: boolean;
  fixture_disclaimer?: string | null;
  message?: string | null;
  summary?: M7EvaluationSummary | null;
}
