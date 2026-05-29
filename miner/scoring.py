from __future__ import annotations

import math
from typing import List

from .models import Product


def score_product(p: Product) -> None:
    """Atribui p.score (0-100) e p.traction_label por fonte.
    Heurística simples e transparente, comparável entre canais."""
    s = 0.0

    if p.sales is not None:  # Mercado Livre / Shopee
        s += min(60.0, 12.0 * math.log10(p.sales + 1))
        p.traction_label = f"{p.sales:,} vendas".replace(",", ".")

    if p.active_days is not None:  # Meta Ad Library
        s += min(40.0, p.active_days * 1.2)
        p.traction_label = f"anúncio ativo há {p.active_days} dias"
    if p.ad_count:
        s += min(20.0, p.ad_count * 2.0)
        extra = f"{p.ad_count} anúncios idênticos"
        p.traction_label = f"{p.traction_label} · {extra}" if p.traction_label else extra

    if p.bsr is not None:  # Amazon — quanto menor o rank, melhor
        s += max(0.0, 50.0 - 8.0 * math.log10(p.bsr + 1))
        p.traction_label = f"BSR #{p.bsr}"

    if p.source == "google":  # produtor direto rodando tráfego
        s += 25.0 if p.ad_count else 12.0
        p.traction_label = "LP patrocinada" if p.ad_count else "domínio orgânico forte"

    # bônus por completude do card (imagem + link)
    if p.image_url:
        s += 5.0
    if p.url:
        s += 3.0

    p.score = round(s, 1)
    if not p.traction_label:
        p.traction_label = "tração não medida"


def rank(products: List[Product], top_n: int) -> List[Product]:
    for p in products:
        score_product(p)
    products.sort(key=lambda x: x.score, reverse=True)
    return products[:top_n]
