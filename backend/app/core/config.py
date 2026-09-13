from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TransformAI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "transformai"
    DATABASE_URL: str | None = None

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            # Ensure asyncpg dialect is used
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    REDIS_URL: str | None = None

    @property
    def async_redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Embeddings Configuration
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Retrieval Configuration (Cosine similarity scale: 0.0 to 1.0)
    DEFAULT_RETRIEVAL_TOP_K: int = 5
    MAX_RETRIEVAL_TOP_K: int = 50
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.0

    # LLM & Generation Configuration
    LLM_PROVIDER: str = "mock"  # "gemini", "openai_compatible", "mock"
    LLM_MODEL: str = "gemini-2.5-flash"
    GEMINI_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_OUTPUT_TOKENS: int = 4096
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 3

    # Multimodal Configuration (Defaults to "mock" for offline/CI execution)
    OCR_PROVIDER: str = "mock"  # "gemini_vision", "tesseract", "mock"
    OCR_MODEL: str = "gemini-2.5-flash"
    OCR_TIMEOUT_SECONDS: int = 60
    TRANSCRIPTION_PROVIDER: str = "mock"  # "gemini_audio", "whisper", "mock"
    TRANSCRIPTION_MODEL: str = "gemini-2.5-flash"
    TRANSCRIPTION_LANGUAGE: str = "en"
    TRANSCRIPTION_TIMEOUT_SECONDS: int = 120

    # Verification Agent Configuration (Milestone 6)
    VERIFICATION_PROVIDER: str = "mock"  # "llm", "mock"
    VERIFICATION_MODEL: str = "gemini-2.5-flash"
    VERIFICATION_TEMPERATURE: float = 0.0
    VERIFICATION_TOP_K: int = 3
    VERIFICATION_SIMILARITY_THRESHOLD: float = 0.2
    VERIFICATION_TIMEOUT_SECONDS: int = 60

    # Modality-Specific File Size Limits
    MAX_TEXT_FILE_SIZE_BYTES: int = 15 * 1024 * 1024     # 15 MB
    MAX_IMAGE_FILE_SIZE_BYTES: int = 20 * 1024 * 1024    # 20 MB
    MAX_AUDIO_FILE_SIZE_BYTES: int = 50 * 1024 * 1024    # 50 MB
    MAX_VIDEO_FILE_SIZE_BYTES: int = 100 * 1024 * 1024   # 100 MB

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
