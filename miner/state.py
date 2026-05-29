from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "state.json"

# Marcas/redes "gigantes" ignoradas por padrão (editável via Telegram).
# Objetivo: tirar só os nomes muito grandes, mantendo marcas emergentes.
_SEED_BLOCKLIST = [
    # multinacionais / grandes marcas
    "loreal", "l'oréal", "l'oreal", "natura", "boticário", "boticario", "avon",
    "nestlé", "nestle", "unilever", "johnson", "bayer", "gsk",
    # grandes redes de farmácia
    "drogal", "drogasil", "droga raia", "drogaraia", "raia", "pague menos",
    "paguemenos", "ultrafarma", "pacheco", "panvel", "são joão", "extrafarma",
    # marketplaces / grandes varejistas
    "amazon", "mercado livre", "mercadolivre", "magazine luiza", "magalu",
    "americanas", "casas bahia", "shopee", "aliexpress",
    # gigantes de suplemento
    "growth suplementos", "max titanium", "integralmedica", "integralmédica",
    "probiótica", "probiotica",
]

_DEFAULT: Dict[str, Any] = {
    "keywords": [],          # nicho escolhido via Telegram; vazio = usa config.yaml
    "telegram_offset": 0,    # último update_id processado do getUpdates
    "amazon_category_url": "",  # opcional: categoria de bestsellers por nicho
    "blocklist": list(_SEED_BLOCKLIST),  # marcas/domínios a ignorar
}


def load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return dict(_DEFAULT)
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT)
    merged = dict(_DEFAULT)
    merged.update(data or {})
    return merged


def save_state(state: Dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def effective_keywords(state: Dict[str, Any], config_keywords: List[str]) -> List[str]:
    """Nicho escolhido pelo Telegram tem prioridade; senão usa o config."""
    kw = state.get("keywords") or []
    return kw if kw else list(config_keywords)
