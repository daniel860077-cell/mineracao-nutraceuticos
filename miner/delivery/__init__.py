from __future__ import annotations

from typing import Any, Dict, List

from ..models import Product
from .telegram import send_telegram
from .discord import send_discord


def deliver(channel: str, products: List[Product], secrets: Dict[str, Any]) -> None:
    if channel == "telegram":
        send_telegram(products, secrets)
    elif channel == "discord":
        send_discord(products, secrets)
    else:
        raise ValueError(f"Canal de entrega desconhecido: {channel}")
