"""
Model / Provider Router — RGS AI Desktop
==========================================
Routes LLM requests to the correct backend:
  • OpenAI GPT family
  • Anthropic Claude
  • Ollama (local)
  • HuggingFace Inference API
  • Fallback: echo mock (for testing)

All agent modules receive a single callable  llm(prompt: str) -> str
via dependency injection.  They never import this module directly —
the orchestration core injects it at startup.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("rgs.model_router")


# ── provider adapters ─────────────────────────────────────────────────────────

def _openai_adapter(
    prompt: str,
    model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    try:
        import openai
        client = openai.OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""
    except ImportError:
        raise RuntimeError("openai package not installed: pip install openai")


def _anthropic_adapter(
    prompt: str,
    model: str = "claude-3-haiku-20240307",
    api_key: Optional[str] = None,
    max_tokens: int = 1024,
) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except ImportError:
        raise RuntimeError("anthropic package not installed: pip install anthropic")


def _ollama_adapter(
    prompt: str,
    model: str = "llama3",
    base_url: str = "http://localhost:11434",
) -> str:
    try:
        import requests
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except ImportError:
        raise RuntimeError("requests not installed: pip install requests")


def _mock_adapter(prompt: str, **_) -> str:
    return f"[Mock LLM] You said: {prompt[:120]}"


# ── ModelRouter ───────────────────────────────────────────────────────────────
class ModelRouter:
    """
    Configurable LLM router.

    Usage:
        router = ModelRouter(provider="openai", model="gpt-4o-mini")
        text = router.ask("What is 2+2?")
        fn   = router.as_callable()   # inject into agents
    """

    PROVIDERS = {
        "openai":    _openai_adapter,
        "anthropic": _anthropic_adapter,
        "ollama":    _ollama_adapter,
        "mock":      _mock_adapter,
    }

    def __init__(
        self,
        provider: str = "mock",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        self._provider = provider
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._call_count = 0
        self._error_count = 0

    def ask(self, prompt: str) -> str:
        adapter = self.PROVIDERS.get(self._provider, _mock_adapter)
        kwargs: Dict[str, Any] = {"prompt": prompt}
        if self._model:
            kwargs["model"] = self._model
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._base_url and self._provider == "ollama":
            kwargs["base_url"] = self._base_url
        kwargs["temperature"] = self._temperature
        kwargs["max_tokens"] = self._max_tokens

        self._call_count += 1
        t0 = time.monotonic()
        try:
            result = adapter(**{k: v for k, v in kwargs.items()
                                if k != "temperature" or self._provider not in ("ollama",)})
            log.debug("LLM [%s] answered in %.2fs", self._provider, time.monotonic() - t0)
            return result
        except Exception as exc:
            self._error_count += 1
            log.error("ModelRouter error (%s): %s", self._provider, exc)
            return f"[LLM Error] {exc}"

    def as_callable(self) -> Callable[[str], str]:
        """Return a simple callable for injection into agents."""
        return self.ask

    def status(self) -> Dict:
        return {
            "provider": self._provider,
            "model": self._model,
            "calls": self._call_count,
            "errors": self._error_count,
        }

    @classmethod
    def from_env(cls) -> "ModelRouter":
        """Auto-configure from environment variables."""
        provider = os.environ.get("RGS_LLM_PROVIDER", "mock")
        model = os.environ.get("RGS_LLM_MODEL")
        api_key = os.environ.get("RGS_LLM_API_KEY")
        base_url = os.environ.get("RGS_LLM_BASE_URL")
        log.info("ModelRouter auto-configured: provider=%s model=%s", provider, model)
        return cls(provider=provider, model=model, api_key=api_key, base_url=base_url)


# ── module-level singleton ────────────────────────────────────────────────────
ROUTER = ModelRouter.from_env()


def smoke_test() -> bool:
    r = ModelRouter(provider="mock")
    resp = r.ask("ping")
    ok = "Mock LLM" in resp
    log.info("ModelRouter smoke_test: %s", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(smoke_test())
