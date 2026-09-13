export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
}

export interface DatabaseHealth {
  status: string;
  connected: boolean;
  latency_ms?: number;
  pgvector_installed: boolean;
  pgvector_version?: string;
  error?: string | null;
}

export interface RedisHealth {
  status: string;
  connected: boolean;
  latency_ms?: number;
  error?: string | null;
}

export interface SystemHealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  database: DatabaseHealth;
  redis: RedisHealth;
}
