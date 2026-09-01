"""Cloud and local LLM gateway for Jinwoo AI.

All provider calls originate in this local backend, never in the React renderer.
Demo mode is deterministic and makes no network request. A non-demo provider is
chosen only after it is configured locally by the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .schemas import ChatResponse, ProviderState, ProviderStatus
from .settings import Settings


class ProviderError(RuntimeError):
    """A safe error suitable for showing in the local Command Center."""


@dataclass(frozen=True)
class ProviderDefinition:
    id: str
    label: str
    mode: str
    configured: bool
    detail: str


class ProviderGateway:
    def __init__(self, config: Settings) -> None:
        self.config = config

    def statuses(self) -> list[ProviderStatus]:
        definitions = [
            ProviderDefinition("ollama", "Ollama", "local", bool(self.config.ollama_model), "Local model runtime"),
            ProviderDefinition("lm-studio", "LM Studio", "local", bool(self.config.lm_studio_model), "Optional OpenAI-compatible local endpoint"),
            ProviderDefinition("claude", "Claude", "cloud", bool(self.config.claude_api_key and self.config.claude_model), "Anthropic Messages API adapter"),
            ProviderDefinition("glm", "GLM / Z.ai", "cloud", bool(self.config.glm_api_key and self.config.glm_base_url and self.config.glm_model), "Configurable GLM/OpenAI-compatible adapter"),
            ProviderDefinition("hugging-face", "Hugging Face", "cloud", bool(self.config.huggingface_api_key and self.config.huggingface_model), "Hosted inference / embeddings adapter"),
            ProviderDefinition("mem0", "Mem0", "memory", bool(self.config.mem0_api_key), "Optional separately consented memory integration; SQLite remains local source of truth"),
        ]
        statuses: list[ProviderStatus] = []
        for item in definitions:
            # A configured Mem0 key is not activation. No sync executor exists
            # until the owner confirms the intended memo API and grants renewed,
            # item-level consent, so preserve SQLite as the visible local source.
            if item.id == "mem0":
                state = ProviderState.OFFLINE
                detail = "Mem0 sync is disabled; local SQLite memory is the source of truth"
            elif item.configured:
                state = ProviderState.READY
                detail = item.detail
            elif item.id == "ollama" and self.config.mode == "demo":
                state = ProviderState.READY
                detail = "Demo-safe local route; choose a model in Settings"
            else:
                state = ProviderState.UNCONFIGURED
                detail = f"{item.detail}; configuration required"
            statuses.append(ProviderStatus(id=item.id, label=item.label, mode=item.mode, state=state, detail=detail))
        return statuses

    def _configured_ids(self) -> set[str]:
        return {status.id for status in self.statuses() if status.state == ProviderState.READY}

    def _choose_provider(self, preferred_provider: str | None, allow_cloud: bool) -> str:
        available = self._configured_ids()
        cloud_providers = {"claude", "glm", "hugging-face"}
        if preferred_provider:
            if preferred_provider not in available:
                raise ProviderError(f"{preferred_provider} is not configured locally. Open Settings before using it.")
            if preferred_provider in cloud_providers and not allow_cloud:
                raise ProviderError("Cloud use needs an explicit approval in the current chat request.")
            return preferred_provider
        for provider_id in ("ollama", "lm-studio", "claude", "glm", "hugging-face"):
            if provider_id in available and (allow_cloud or provider_id not in cloud_providers):
                return provider_id
        if available.intersection(cloud_providers) and not allow_cloud:
            raise ProviderError("Only cloud providers are configured. Explicitly approve cloud use or configure a local model.")
        raise ProviderError("No live provider is configured. Start Ollama/LM Studio or add one cloud provider in local Settings.")

    async def chat(self, message: str, preferred_provider: str | None = None, allow_cloud: bool = False) -> ChatResponse:
        if self.config.mode == "demo":
            del preferred_provider, allow_cloud
            return ChatResponse(
                reply=(
                    "Demo mode is active. Jinwoo has received the order and can create a visible mission plan. "
                    "Configure Ollama, LM Studio, Claude, GLM, or Hugging Face locally before requesting a live model run."
                ),
                provider="ollama-demo",
                local_only=True,
            )

        provider_id = self._choose_provider(preferred_provider, allow_cloud)
        if provider_id == "ollama":
            content = await self._ollama_chat(message)
        elif provider_id == "lm-studio":
            content = await self._openai_compatible_chat(
                base_url=self.config.lm_studio_base_url,
                api_key="",
                model=self.config.lm_studio_model,
                message=message,
            )
        elif provider_id == "claude":
            content = await self._claude_chat(message)
        elif provider_id == "glm":
            content = await self._openai_compatible_chat(
                base_url=self.config.glm_base_url,
                api_key=self.config.glm_api_key,
                model=self.config.glm_model,
                message=message,
            )
        elif provider_id == "hugging-face":
            content = await self._hugging_face_chat(message)
        else:  # defensive: _choose_provider returns only the supported provider ids
            raise ProviderError(f"Unsupported provider: {provider_id}")

        return ChatResponse(reply=content, provider=provider_id, local_only=provider_id in {"ollama", "lm-studio"})

    async def _ollama_chat(self, message: str) -> str:
        if not self.config.ollama_model:
            raise ProviderError("Set JINWOO_OLLAMA_MODEL after pulling a local Ollama model.")
        payload = {
            "model": self.config.ollama_model,
            "stream": False,
            "messages": [
                {"role": "system", "content": "You are Jinwoo AI. Be concise, useful, transparent and approval-first."},
                {"role": "user", "content": message},
            ],
        }
        response = await self._post_json(f"{self.config.ollama_base_url}/api/chat", payload)
        content = response.get("message", {}).get("content")
        return self._require_text(content, "Ollama")

    async def _openai_compatible_chat(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        message: str = "",
    ) -> str:
        if not model:
            raise ProviderError("Select a model for this local/provider endpoint.")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are Jinwoo AI. Be concise, useful, transparent and approval-first."},
                {"role": "user", "content": message},
            ],
            "temperature": 0.4,
        }
        response = await self._post_json(f"{base_url.rstrip('/')}/chat/completions", payload, headers=headers)
        choices = response.get("choices")
        content = choices[0].get("message", {}).get("content") if isinstance(choices, list) and choices else None
        return self._require_text(content, "OpenAI-compatible provider")

    async def _claude_chat(self, message: str) -> str:
        if not self.config.claude_api_key or not self.config.claude_model:
            raise ProviderError("Set JINWOO_CLAUDE_API_KEY and JINWOO_CLAUDE_MODEL locally first.")
        payload = {
            "model": self.config.claude_model,
            "max_tokens": 1024,
            "system": "You are Jinwoo AI. Be concise, useful, transparent and approval-first.",
            "messages": [{"role": "user", "content": message}],
        }
        response = await self._post_json(
            "https://api.anthropic.com/v1/messages",
            payload,
            headers={
                "x-api-key": self.config.claude_api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        blocks = response.get("content")
        content = blocks[0].get("text") if isinstance(blocks, list) and blocks else None
        return self._require_text(content, "Claude")

    async def _hugging_face_chat(self, message: str) -> str:
        if not self.config.huggingface_api_key or not self.config.huggingface_model:
            raise ProviderError("Set JINWOO_HUGGINGFACE_API_KEY and JINWOO_HUGGINGFACE_MODEL locally first.")
        # This endpoint is configurable in the next settings milestone because
        # Hugging Face supports multiple inference providers. The default route
        # is intentionally a standard hosted-inference shape, not an automatic
        # model download.
        endpoint = f"https://router.huggingface.co/hf-inference/models/{self.config.huggingface_model}"
        response = await self._post_json(
            endpoint,
            {"inputs": message, "parameters": {"max_new_tokens": 512, "return_full_text": False}},
            headers={"Authorization": f"Bearer {self.config.huggingface_api_key}"},
        )
        if isinstance(response, list) and response:
            content = response[0].get("generated_text") if isinstance(response[0], dict) else None
        else:
            content = response.get("generated_text") if isinstance(response, dict) else None
        return self._require_text(content, "Hugging Face")

    async def _post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> Any:
        merged_headers = {"Content-Type": "application/json", **(headers or {})}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=12.0)) as client:
                response = await client.post(url, json=payload, headers=merged_headers)
        except httpx.HTTPError as error:
            raise ProviderError(f"Provider connection failed: {error.__class__.__name__}") from error
        if response.is_error:
            detail = response.text[:240].replace("\n", " ")
            raise ProviderError(f"Provider returned HTTP {response.status_code}: {detail}")
        try:
            return response.json()
        except ValueError as error:
            raise ProviderError("Provider returned a non-JSON response.") from error

    @staticmethod
    def _require_text(value: Any, provider: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ProviderError(f"{provider} returned no readable assistant text.")
        return value.strip()
