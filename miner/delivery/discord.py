from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List

import requests

from ..models import Product

log = logging.getLogger("miner.delivery.discord")

SOURCE_LABEL = {
    "meta_ads": "Meta Ad Library",
    "mercado_livre": "Mercado Livre",
    "shopee": "Shopee",
    "amazon": "Amazon",
    "google": "Google",
}


def _embed(p: Product, idx: int) -> dict:
    fields = [{"name": "Tração", "value": f"{p.traction_label} (score {p.score})", "inline": True}]
    if p.seller:
        fields.append({"name": "Anunciante/Loja", "value": p.seller[:200], "inline": True})
    if p.keyword:
        fields.append({"name": "Keyword", "value": p.keyword, "inline": True})
    embed = {
        "title": f"#{idx} — {p.name[:240]}",
        "url": p.url or None,
        "description": SOURCE_LABEL.get(p.source, p.source),
        "fields": fields,
    }
    if p.image_url:
        embed["image"] = {"url": p.image_url}
    return embed


def send_discord(products: List[Product], secrets: Dict[str, Any]) -> None:
    webhook = secrets.get("discord_webhook_url")
    if not webhook:
        raise RuntimeError("DISCORD_WEBHOOK_URL não configurado.")

    header = f"🧪 **Mineração de Nutracêuticos — {date.today():%d/%m/%Y}** — {len(products)} produtos validados."
    requests.post(webhook, json={"content": header}, timeout=30)

    # Discord aceita até 10 embeds por mensagem
    embeds = [_embed(p, i) for i, p in enumerate(products, 1)]
    for chunk_start in range(0, len(embeds), 10):
        chunk = embeds[chunk_start:chunk_start + 10]
        try:
            requests.post(webhook, json={"embeds": chunk}, timeout=30)
        except requests.RequestException as exc:
            log.warning("Falha ao enviar embeds Discord: %s", exc)
