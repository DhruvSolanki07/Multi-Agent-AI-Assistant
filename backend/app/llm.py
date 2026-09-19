from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from .config import Settings


class LLMError(RuntimeError):
    pass


class LLMClient:
    """Thin async client for OpenAI-compatible and Anthropic chat endpoints."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._httpx = httpx.AsyncClient(timeout=60.0)

    @property
    def configured(self) -> bool:
        return self.settings.llm_configured

    async def aclose(self) -> None:
        await self._httpx.aclose()

    @staticmethod
    def _provider_for(settings: Settings) -> str:
        return settings.llm_provider.lower().lstrip("anthropic").strip()

    async def complete_json(self, system: str, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
        """Return parsed JSON dict. Falls back to `fallback` if provider is unset or errors."""
        if not self.configured:
            return fallback
        try:
            text = await self._chat(system, prompt)
            return json.loads(text.split("json")[-1].strip().strip("`\n") or text)
        except Exception as exc:  # noqa: BLE001 - provider failure should degrade gracefully
            raise LLMError(f"LLM call failed: {exc}") from exc

    async def complete_text(self, system: str, user: str, default: str = "") -> str:
        if not self.configured:
            return default
        try:
            return (await self._chat(system, user)).strip()
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"LLM call failed: {exc}") from exc

    async def _chat(self, system: str, user: str) -> str:
        s = self.settings
        provider = s.llm_provider
        if provider == "anthropic" and s.anthropic_api_key:
            return await self._chat_anthropic(system, user)
        # Default: OpenAI-compatible (real OpenAI, LM Studio, Ollama, vLLM...)
        return await self._chat_openai(system, user)

    async def _chat_openai(self, system: str, user: str, warmup=False) -> str:
        s = self.settings
        key = s.llm_api_key or s.openai_api_key
        payload = {
            "model": s.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
        }
        headers = {"Authorization": f"Bearer {key}"}
        r = await self._httpx.post(
            f"{s.base_url}/chat/completions", json=payload, headers=headers
        )
        if r.status_code >= 400:
            raise LLMError(f"HTTP {r.status_code}: {r.text[:400]}")
        data = r.json()
        return data["choices"][0]["message"]["content"]

    async def _chat_anthropic(self, system: str, user: str) -> str:
        s = self.settings
        payload = {
            "model": s.anthropic_model,
            "max_tokens": 4096,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": s.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        }
        r = await self._httpx.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
        data = r.json()
        return "".join(b.get("text", "") for b in data.get("content", []))


async def stream_text(text: str) -> AsyncIterator[str]:
    """Split a string into SSE-appropriate chunks (used for report streaming)."""
    for i in range(0, len(text), 120):
        yield text[i : i + 120]
        await __import__("asyncio").sleep(0)  # yield control to the loop