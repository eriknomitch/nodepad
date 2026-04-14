"""Configuration management — replaces browser localStorage with file-based config."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".nodepad"
CONFIG_FILE = CONFIG_DIR / "config.json"

PROVIDERS = {
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
    },
    "zai": {
        "label": "Z.ai",
        "base_url": "https://api.z.ai/api/paas/v4",
    },
}

DEFAULT_PROVIDER = "openrouter"
DEFAULT_MODEL_ID = "openai/gpt-4o"


@dataclass
class AIConfig:
    api_key: str
    model_id: str
    provider: str
    web_grounding: bool = False
    custom_base_url: str = ""

    @property
    def base_url(self) -> str:
        if self.custom_base_url:
            return self.custom_base_url
        return PROVIDERS.get(self.provider, PROVIDERS["openrouter"])["base_url"]

    def get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://nodepad.space"
            headers["X-Title"] = "nodepad-cli"
        return headers


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """Load config from ~/.nodepad/config.json, with env var overrides."""
    config: dict[str, Any] = {
        "provider": DEFAULT_PROVIDER,
        "model_id": DEFAULT_MODEL_ID,
        "api_key": "",
        "web_grounding": False,
        "custom_base_url": "",
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass

    # Env var overrides
    if env_key := os.environ.get("NODEPAD_API_KEY"):
        config["api_key"] = env_key
    if env_provider := os.environ.get("NODEPAD_PROVIDER"):
        config["provider"] = env_provider
    if env_model := os.environ.get("NODEPAD_MODEL"):
        config["model_id"] = env_model
    if env_base := os.environ.get("NODEPAD_BASE_URL"):
        config["custom_base_url"] = env_base

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save config to ~/.nodepad/config.json."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_ai_config() -> AIConfig | None:
    """Load and return an AIConfig ready for API calls. Returns None if no API key."""
    config = load_config()
    api_key = config.get("api_key", "")
    if not api_key:
        return None
    return AIConfig(
        api_key=api_key,
        model_id=config.get("model_id", DEFAULT_MODEL_ID),
        provider=config.get("provider", DEFAULT_PROVIDER),
        web_grounding=config.get("web_grounding", False),
        custom_base_url=config.get("custom_base_url", ""),
    )
