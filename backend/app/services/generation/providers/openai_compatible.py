import time
import asyncio
import logging
from typing import Optional
import httpx

from app.core.config import settings
from app.services.generation.base import BaseLLMProvider, GenerationRequest, GenerationResponse

logger = logging.getLogger("transformai.llm.openai")


class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Asynchronous provider for OpenAI-compatible REST endpoints (OpenAI, Groq, DeepSeek, Ollama, vLLM).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = (base_url or settings.OPENAI_API_BASE).rstrip("/")
        self.model = model_name or settings.LLM_MODEL
        self.timeout = timeout_seconds or settings.LLM_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.LLM_MAX_RETRIES

    @property
    def provider_name(self) -> str:
        return "openai_compatible"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        url = f"{self.base_url}/chat/completions"

        messages = []
        if request.system_instruction:
            messages.append({"role": "system", "content": request.system_instruction})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": request.temperature,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.response_format_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        t0 = time.perf_counter()
        last_exception: Optional[Exception] = None

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.debug("Executing OpenAI-compatible request (attempt %d/%d)...", attempt, self.max_retries)
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 200:
                        data = response.json()
                        latency_ms = (time.perf_counter() - t0) * 1000

                        choices = data.get("choices", [])
                        if not choices:
                            raise ValueError(f"OpenAI API returned no choices: {data}")

                        content = choices[0].get("message", {}).get("content", "")
                        finish_reason = choices[0].get("finish_reason")

                        usage = None
                        if "usage" in data and isinstance(data["usage"], dict):
                            u = data["usage"]
                            usage = {
                                "prompt_tokens": u.get("prompt_tokens", 0),
                                "completion_tokens": u.get("completion_tokens", 0),
                                "total_tokens": u.get("total_tokens", 0),
                            }

                        return GenerationResponse(
                            content=content,
                            model_name=self.model,
                            provider_name=self.provider_name,
                            finish_reason=finish_reason,
                            usage=usage,
                            latency_ms=round(latency_ms, 2),
                        )

                    elif response.status_code in [429, 500, 502, 503, 504]:
                        logger.warning(
                            "OpenAI transient HTTP %d error. Retrying in %d seconds...",
                            response.status_code,
                            2 ** attempt,
                        )
                        await asyncio.sleep(2 ** attempt)
                    else:
                        err_msg = f"OpenAI API returned HTTP {response.status_code}: {response.text}"
                        logger.error("OpenAI API error: %s", err_msg)
                        raise RuntimeError(err_msg)

                except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                    last_exception = net_err
                    logger.warning("OpenAI network/timeout error (attempt %d): %s", attempt, net_err)
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"OpenAI generation failed after {self.max_retries} attempts: {last_exception}")
