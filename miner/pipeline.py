from __future__ import annotations

import logging
from typing import Any, Dict, List

from .db import Store
from .delivery import deliver
from .models import Product
from .scoring import rank
from .sources import REGISTRY
from .sources.base import ApifyRunner
from .state import effective_keywords, load_state, save_state
from .telegram_commands import process_commands

log = logging.getLogger("miner.pipeline")


def run(cfg: Dict[str, Any], dry_run: bool = False) -> List[Product]:
    secrets = cfg["secrets"]
    runner = ApifyRunner(secrets["apify_token"])

    # 0) Lê comandos do Telegram (ex: /buscar ...) e aplica o nicho escolhido
    state = load_state()
    state, changed = process_commands(secrets, state)
    if changed:
        save_state(state)
    keywords = effective_keywords(state, cfg["keywords"])

    # Categoria de bestsellers da Amazon pode ser sobrescrita por nicho
    amz_url = state.get("amazon_category_url")
    if amz_url and "amazon" in cfg["sources"]:
        cfg["sources"]["amazon"]["category_url"] = amz_url

    log.info("Nicho desta execução: %s", ", ".join(keywords))

    # 1) Coleta em todas as fontes habilitadas
    collected: List[Product] = []
    for name, src_cfg in cfg["sources"].items():
        if not src_cfg.get("enabled"):
            continue
        cls = REGISTRY.get(name)
        if not cls:
            log.warning("Fonte desconhecida no config: %s", name)
            continue
        log.info("Coletando fonte: %s", name)
        try:
            items = cls(runner, src_cfg, cfg).collect(keywords)
            log.info("%s -> %d produtos brutos", name, len(items))
            collected.extend(items)
        except Exception as exc:  # noqa: BLE001
            log.exception("Fonte %s falhou completamente: %s", name, exc)

    log.info("Total coletado: %d", len(collected))

    # 2) Deduplicação na janela de N dias (SQLite)
    store = Store()
    window = int(cfg.get("dedup_window_days", 15))
    fresh = store.filter_new(collected, window)
    log.info("Após dedup (%dd): %d", window, len(fresh))

    # 3) Score + ranking, seleciona os melhores do dia
    top = rank(fresh, int(cfg.get("daily_count", 6)))
    log.info("Selecionados para entrega: %d", len(top))

    if dry_run:
        store.close()
        return top

    # 4) Entrega + marca como entregue
    if top:
        deliver(cfg.get("delivery", "telegram"), top, secrets)
        store.mark_delivered(top)
    else:
        log.warning("Nenhum produto novo para entregar hoje.")

    store.close()
    return top
