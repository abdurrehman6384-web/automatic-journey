"""Environment-only configuration. Secrets never belong in the browser bundle."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    mode: str
    data_dir: Path
    claude_api_key: str
    claude_model: str
    glm_api_key: str
    glm_base_url: str
    glm_model: str
    huggingface_api_key: str
    huggingface_model: str
    mem0_api_key: str
    ollama_base_url: str
    ollama_model: str
    lm_studio_base_url: str
    lm_studio_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        data_dir = Path(os.getenv("JINWOO_DATA_DIR", "./data")).expanduser().resolve()
        return cls(
            mode=os.getenv("JINWOO_MODE", "demo").strip().lower(),
            data_dir=data_dir,
            claude_api_key=os.getenv("JINWOO_CLAUDE_API_KEY", "").strip(),
            claude_model=os.getenv("JINWOO_CLAUDE_MODEL", "").strip(),
            glm_api_key=os.getenv("JINWOO_GLM_API_KEY", "").strip(),
            glm_base_url=os.getenv("JINWOO_GLM_BASE_URL", "").strip(),
            glm_model=os.getenv("JINWOO_GLM_MODEL", "").strip(),
            huggingface_api_key=os.getenv("JINWOO_HUGGINGFACE_API_KEY", "").strip(),
            huggingface_model=os.getenv("JINWOO_HUGGINGFACE_MODEL", "").strip(),
            mem0_api_key=os.getenv("JINWOO_MEM0_API_KEY", "").strip(),
            ollama_base_url=os.getenv("JINWOO_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
            ollama_model=os.getenv("JINWOO_OLLAMA_MODEL", "").strip(),
            lm_studio_base_url=os.getenv("JINWOO_LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/"),
            lm_studio_model=os.getenv("JINWOO_LM_STUDIO_MODEL", "").strip(),
        )


settings = Settings.from_env()
