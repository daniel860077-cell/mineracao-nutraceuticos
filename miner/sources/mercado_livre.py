from __future__ import annotations

import logging
from typing import List

from .base import Source
from ._util import parse_int
from ..models import Product

log = logging.getLogger("miner.sources.ml")


class MercadoLivreSource(Source):
    """Mercado Livre — busca por palavra-chave, ordenada por mais vendidos.
    Validação = nº de vendas declaradas na página do produto."""

    name = "mercado_livre"

    def collect(self, keywords: List[str]) -> List[Product]:
        actor = self.cfg["actor_id"]
        min_sales = int(self.cfg.get("min_sales", 50))
        max_pages = int(self.cfg.get("max_pages", 2))
        promoted = bool(self.cfg.get("promoted", True))
        products: List[Product] = []

        for kw in keywords:
            run_input = {
                "keyword": kw,
                "maxPages": max_pages,
                "promoted": promoted,
            }
            try:
                items = self.runner.run(actor, run_input)
            except Exception as exc:  # noqa: BLE001
                log.warning("Mercado Livre falhou para '%s': %s", kw, exc)
                continue

            for it in items:
                sales = parse_int(
                    self._first(
                        it, "soldQuantity", "sold_quantity", "sales", "soldText",
                        "vendidos", "quantidadeVendida", "qtdVendida",
                    )
                )
                if sales is not None and sales < min_sales:
                    continue

                name = self._first(it, "title", "name", "titulo", "nome", default=kw)
                products.append(
                    Product(
                        name=str(name),
                        source=self.name,
                        url=str(self._first(it, "url", "permalink", "link", default="")),
                        image_url=self._first(
                            it, "thumbnail", "image", "pictureUrl", "img", "imagem", "foto"
                        ),
                        seller=self._first(
                            it, "sellerName", "seller", "official_store_name",
                            "vendedor", "loja",
                        ),
                        keyword=kw,
                        sales=sales,
                        raw=it,
                    )
                )
        return products
