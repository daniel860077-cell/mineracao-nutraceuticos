from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: str | None = None) -> Dict[str, Any]:
    """Carrega config.yaml e injeta segredos do .env."""
    load_dotenv(ROOT / ".env")

    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    cfg["secrets"] = {
        "apify_token": os.getenv("APIFY_TOKEN", ""),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "discord_webhook_url": os.getenv("DISCORD_WEBHOOK_URL", ""),
    }

    if not cfg["secrets"]["apify_token"]:
        raise RuntimeError(
            "APIFY_TOKEN não definido. Copie .env.example para .env e preencha."
        )

    return cfg
