import time
import json
import asyncio
import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.services.generation.base import BaseLLMProvider, GenerationRequest, GenerationResponse

logger = logging.getLogger("transformai.llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """
    Direct asynchronous REST provider for Google Gemini models.
    Provides structured JSON generation, exponential backoff retries, and token telemetry without heavy SDK overhead.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model_name or settings.LLM_MODEL
        self.timeout = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.LLM_MAX_RETRIES

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings or environment.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        # 1. Assemble payload
        contents = [{"role": "user", "parts": [{"text": request.prompt}]}]
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens or settings.LLM_MAX_OUTPUT_TOKENS,
            },
        }

        if request.system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": request.system_instruction}]
            }

        if request.response_format_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        # 2. Execute request with retries
        headers = {"Content-Type": "application/json"}
        last_exception: Optional[Exception] = None

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.debug("Executing Gemini request (attempt %d/%d)...", attempt, self.max_retries)
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        latency_ms = (time.perf_counter() - t0) * 1000

                        candidates = data.get("candidates", [])
                        if not candidates:
                            raise ValueError(f"Gemini API returned no generation candidates: {data}")

                        content_parts = candidates[0].get("content", {}).get("parts", [])
                        generated_text = "".join(p.get("text", "") for p in content_parts)
                        finish_reason = candidates[0].get("finishReason")

                        # Extract actual token usage metadata if provided
                        usage = None
                        if "usageMetadata" in data:
                            u_meta = data["usageMetadata"]
                            usage = {
                                "prompt_tokens": u_meta.get("promptTokenCount", 0),
                                "completion_tokens": u_meta.get("candidatesTokenCount", 0),
                                "total_tokens": u_meta.get("totalTokenCount", 0),
                            }

                        return GenerationResponse(
                            content=generated_text,
                            model_name=self.model,
                            provider_name=self.provider_name,
                            finish_reason=finish_reason,
                            usage=usage,
                            latency_ms=round(latency_ms, 2),
                        )

                    elif response.status_code in [429, 500, 502, 503, 504]:
                        logger.warning(
                            "Gemini transient HTTP %d error. Retrying in %d seconds...",
                            response.status_code,
                            2 ** attempt,
                        )
                        await asyncio.sleep(2 ** attempt)
                    else:
                        err_msg = f"Gemini API returned HTTP {response.status_code}: {response.text}"
                        logger.error("Gemini API error: %s", err_msg)
                        raise RuntimeError(err_msg)

                except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                    last_exception = net_err
                    logger.warning("Gemini network/timeout error (attempt %d): %s", attempt, net_err)
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"Gemini generation failed after {self.max_retries} attempts: {last_exception}")
