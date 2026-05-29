from __future__ import annotations

import logging
from typing import List

from .base import Source
from ._util import parse_int
from ..models import Product

log = logging.getLogger("miner.sources.shopee")


class ShopeeSource(Source):
    """Shopee — busca por palavra-chave ordenada por mais vendidos.
    Validação = volume de vendas exibido na listagem."""

    name = "shopee"

    def collect(self, keywords: List[str]) -> List[Product]:
        actor = self.cfg["actor_id"]
        min_sales = int(self.cfg.get("min_sales", 100))
        cap = int(self.cfg.get("max_items_per_keyword", 30))
        products: List[Product] = []

        for kw in keywords:
            run_input = {
                "location": kw,
                "country": self.g.get("country", "BR"),
                "maxItems": cap,
            }
            try:
                items = self.runner.run(actor, run_input)
            except Exception as exc:  # noqa: BLE001
                log.warning("Shopee falhou para '%s': %s", kw, exc)
                continue

            for it in items:
                sales = parse_int(
                    self._first(it, "sold", "historicalSold", "sales", "soldCount")
                )
                if sales is not None and sales < min_sales:
                    continue

                name = self._first(it, "name", "title", default=kw)
                products.append(
                    Product(
                        name=str(name),
                        source=self.name,
                        url=str(self._first(it, "url", "productUrl", "link", default="")),
                        image_url=self._first(it, "image", "imageUrl", "thumbnail"),
                        seller=self._first(it, "shopName", "seller", "shop"),
                        keyword=kw,
                        sales=sales,
                        raw=it,
                    )
                )
        return products
