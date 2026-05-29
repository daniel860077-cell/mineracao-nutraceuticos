from __future__ import annotations

import logging
from typing import List
from urllib.parse import urlparse

from .base import Source
from ..models import Product

log = logging.getLogger("miner.sources.google")

# domínios de marketplaces/portais — não são "produtores diretos"
_SKIP_DOMAINS = (
    "mercadolivre", "mercadolibre", "amazon.", "shopee", "magazineluiza",
    "americanas", "casasbahia", "wikipedia", "youtube", "instagram",
    "facebook", "globo.com", "drogaria", "drogasil", "paguemenos",
)


class GoogleSource(Source):
    """Google Search — resultados orgânicos + anúncios patrocinados.
    Validação = presença de domínios novos / landing pages estruturadas
    (VSL / venda direta) de produtores rodando tráfego."""

    name = "google"

    def collect(self, keywords: List[str]) -> List[Product]:
        actor = self.cfg["actor_id"]
        products: List[Product] = []

        for kw in keywords:
            run_input = {
                "queries": kw,
                "maxPagesPerQuery": 1,
                "countryCode": self.g.get("country", "br").lower(),
                "languageCode": self.g.get("language", "pt-BR"),
            }
            try:
                items = self.runner.run(actor, run_input)
            except Exception as exc:  # noqa: BLE001
                log.warning("Google falhou para '%s': %s", kw, exc)
                continue

            for page in items:
                organic = page.get("organicResults") or []
                paid = page.get("paidResults") or []
                for res in paid + organic:
                    url = res.get("url") or res.get("link") or ""
                    host = urlparse(url).netloc.lower()
                    if not host or any(s in host for s in _SKIP_DOMAINS):
                        continue
                    products.append(
                        Product(
                            name=str(res.get("title") or kw),
                            source=self.name,
                            url=url,
                            seller=host.replace("www.", ""),
                            keyword=kw,
                            ad_count=1 if res in paid else None,
                            raw={"isPaid": res in paid, "description": res.get("description")},
                        )
                    )
        return products
