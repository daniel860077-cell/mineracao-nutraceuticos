from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Optional


def _slug(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text[:80]


@dataclass
class Product:
    """Produto minerado, normalizado entre todas as fontes."""

    name: str                       # Nome comercial
    source: str                     # meta_ads | mercado_livre | shopee | amazon | google
    url: str                        # Link direto (loja / anúncio / listagem)
    image_url: Optional[str] = None
    seller: Optional[str] = None    # Marca / loja / anunciante
    keyword: Optional[str] = None   # Palavra-chave que originou o achado

    # Tração / validação (preenchido conforme a fonte)
    sales: Optional[int] = None         # nº de vendas (marketplaces)
    active_days: Optional[int] = None   # tempo de veiculação (Meta)
    ad_count: Optional[int] = None      # nº de anúncios idênticos (Meta)
    bsr: Optional[int] = None           # Best Sellers Rank (Amazon)

    score: float = 0.0
    traction_label: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        """Identidade estável p/ deduplicação (nome normalizado + fonte)."""
        base = f"{self.source}:{_slug(self.name)}"
        return hashlib.sha1(base.encode("utf-8")).hexdigest()
