from __future__ import annotations

from typing import Iterable, List
from urllib.parse import urlparse

from .models import Product


def _haystack(p: Product) -> str:
    """Texto onde procurar marcas bloqueadas: vendedor + domínio + nome."""
    domain = ""
    if p.url:
        domain = urlparse(p.url).netloc.lower().replace("www.", "")
    parts = [p.seller or "", domain, p.name or ""]
    return " ".join(parts).lower()


def is_blocked(p: Product, blocklist: Iterable[str]) -> bool:
    hay = _haystack(p)
    for term in blocklist:
        t = (term or "").strip().lower()
        if t and t in hay:
            return True
    return False


def apply_blocklist(products: List[Product], blocklist: Iterable[str]) -> List[Product]:
    bl = [t for t in blocklist if t]
    if not bl:
        return list(products)
    return [p for p in products if not is_blocked(p, bl)]
