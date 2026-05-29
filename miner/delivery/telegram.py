from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List

import requests

from ..models import Product

log = logging.getLogger("miner.delivery.telegram")

SOURCE_LABEL = {
    "meta_ads": "Meta Ad Library",
    "mercado_livre": "Mercado Livre",
    "shopee": "Shopee",
    "amazon": "Amazon",
    "google": "Google",
}


def _caption(p: Product, idx: int) -> str:
    src = SOURCE_LABEL.get(p.source, p.source)
    lines = [
        f"<b>#{idx} — {_esc(p.name)}</b>",
        f"📦 Fonte: {src}",
        f"📈 Tração: {_esc(p.traction_label)} (score {p.score})",
    ]
    if p.seller:
        lines.append(f"🏷️ Anunciante/Loja: {_esc(p.seller)}")
    if p.keyword:
        lines.append(f"🔑 Keyword: {_esc(p.keyword)}")
    if p.url:
        lines.append(f"🔗 <a href=\"{p.url}\">Abrir origem</a>")
    return "\n".join(lines)


def _esc(text: str | None) -> str:
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def send_telegram(products: List[Product], secrets: Dict[str, Any]) -> None:
    token = secrets.get("telegram_bot_token")
    chat_id = secrets.get("telegram_chat_id")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID não configurados.")

    base = f"https://api.telegram.org/bot{token}"
    header = f"🧪 <b>Mineração de Nutracêuticos — {date.today():%d/%m/%Y}</b>\n{len(products)} produtos validados hoje."
    requests.post(f"{base}/sendMessage", json={
        "chat_id": chat_id, "text": header, "parse_mode": "HTML",
    }, timeout=30)

    for idx, p in enumerate(products, 1):
        caption = _caption(p, idx)
        try:
            if p.image_url:
                r = requests.post(f"{base}/sendPhoto", json={
                    "chat_id": chat_id, "photo": p.image_url,
                    "caption": caption, "parse_mode": "HTML",
                }, timeout=30)
                if r.ok:
                    continue
            # fallback sem imagem (ou se sendPhoto recusar a URL)
            requests.post(f"{base}/sendMessage", json={
                "chat_id": chat_id, "text": caption,
                "parse_mode": "HTML", "disable_web_page_preview": False,
            }, timeout=30)
        except requests.RequestException as exc:
            log.warning("Falha ao enviar produto %d: %s", idx, exc)
