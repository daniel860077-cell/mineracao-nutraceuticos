from __future__ import annotations

import logging
from typing import List

from .base import Source
from ._util import parse_int
from ..models import Product

log = logging.getLogger("miner.sources.amazon")


class AmazonSource(Source):
    """Amazon — categoria Saúde e Cuidados Pessoais (Best Sellers).
    Validação = ranking de mais vendidos (BSR). Não usa keywords;
    minera a lista de bestsellers da categoria."""

    name = "amazon"

    def collect(self, keywords: List[str]) -> List[Product]:
        actor = self.cfg["actor_id"]
        cap = int(self.cfg.get("max_items", 50))
        cat_url = self.cfg.get("category_url")
        products: List[Product] = []

        run_input = {
            "categoryUrls": [cat_url] if cat_url else [],
            "maxItemsPerStartUrl": cap,
        }
        try:
            items = self.runner.run(actor, run_input)
        except Exception as exc:  # noqa: BLE001
            log.warning("Amazon falhou: %s", exc)
            return products

        kw_lower = [k.lower() for k in keywords]
        for it in items:
            name = self._first(it, "title", "name", default="")
            if not name:
                continue
            # filtra ao nicho de encapsulados/suplementos pelas keywords
            matched = next((k for k in kw_lower if k in str(name).lower()), None)

            products.append(
                Product(
                    name=str(name),
                    source=self.name,
                    url=str(self._first(it, "url", "link", default="")),
                    image_url=self._first(it, "image", "thumbnail", "imageUrl"),
                    seller=self._first(it, "brand", "seller", "manufacturer"),
                    keyword=matched,
                    bsr=parse_int(self._first(it, "bestSellerRank", "rank", "position")),
                    raw=it,
                )
            )
        # se houver keywords casadas, prioriza-as; senão devolve a categoria toda
        nicho = [p for p in products if p.keyword]
        return nicho if nicho else products
