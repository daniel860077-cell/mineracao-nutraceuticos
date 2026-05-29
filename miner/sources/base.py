from __future__ import annotations

import logging
from typing import Any, Dict, List

from apify_client import ApifyClient

from ..models import Product

log = logging.getLogger("miner.sources")


class ApifyRunner:
    """Executa um actor da Apify e devolve os itens do dataset."""

    def __init__(self, token: str):
        self.client = ApifyClient(token)

    def run(self, actor_id: str, run_input: Dict[str, Any]) -> List[dict]:
        log.info("Apify actor=%s input=%s", actor_id, {k: run_input[k] for k in list(run_input)[:3]})
        run = self.client.actor(actor_id).call(run_input=run_input)
        if not run or not run.get("defaultDatasetId"):
            log.warning("Actor %s sem dataset de saída", actor_id)
            return []
        items = self.client.dataset(run["defaultDatasetId"]).list_items().items
        log.info("Actor %s retornou %d itens", actor_id, len(items))
        return items


class Source:
    """Contrato base de uma fonte. Cada subclasse mapeia o output do actor
    para uma lista de Product."""

    name: str = "base"

    def __init__(self, runner: ApifyRunner, cfg: Dict[str, Any], global_cfg: Dict[str, Any]):
        self.runner = runner
        self.cfg = cfg
        self.g = global_cfg

    def collect(self, keywords: List[str]) -> List[Product]:
        raise NotImplementedError

    @staticmethod
    def _first(d: dict, *keys, default=None):
        """Pega o primeiro campo presente (schemas de actors variam)."""
        for k in keys:
            v = d.get(k)
            if v not in (None, "", []):
                return v
        return default
