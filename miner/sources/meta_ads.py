from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List
from urllib.parse import quote_plus

from .base import Source
from ..models import Product

log = logging.getLogger("miner.sources.meta")


def _ad_library_url(keyword: str, country: str) -> str:
    return (
        "https://www.facebook.com/ads/library/?active_status=active"
        f"&ad_type=all&country={country}&q={quote_plus(keyword)}"
        "&search_type=keyword_unordered&media_type=all"
    )


def _parse_days_active(item: dict) -> int | None:
    start = (
        item.get("startDate")
        or item.get("ad_delivery_start_time")
        or item.get("startDateFormatted")
    )
    if not start:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(str(start)[: len(fmt) + 5], fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0, (datetime.now(timezone.utc) - dt).days)
        except ValueError:
            continue
    return None


class MetaAdsSource(Source):
    """Meta Ad Library. Validação = tempo de veiculação (anúncio ativo
    há > min_active_days) e quantidade de anúncios idênticos por página."""

    name = "meta_ads"

    def collect(self, keywords: List[str]) -> List[Product]:
        actor = self.cfg["actor_id"]
        min_days = int(self.cfg.get("min_active_days", 5))
        cap = int(self.cfg.get("count_per_keyword", 30))
        country = self.g.get("country", "BR")
        products: List[Product] = []

        for kw in keywords:
            run_input = {
                "urls": [_ad_library_url(kw, country)],
                "count": cap,
                "scrapeAdDetails": True,
                "scrapePageAds.activeStatus": "active",
                "scrapePageAds.countryCode": country,
            }
            try:
                items = self.runner.run(actor, run_input)
            except Exception as exc:  # noqa: BLE001
                log.warning("Meta falhou para '%s': %s", kw, exc)
                continue

            for it in items:
                active_days = _parse_days_active(it)
                if active_days is not None and active_days < min_days:
                    continue

                name = self._first(
                    it, "pageName", "page_name", "advertiserName", "title",
                    default=kw,
                )
                image = self._first(
                    it, "imageUrl", "image", "originalImageUrl", "thumbnailUrl",
                )
                if not image:
                    snaps = it.get("snapshot") or {}
                    cards = snaps.get("cards") or []
                    if cards:
                        image = cards[0].get("original_image_url") or cards[0].get("resized_image_url")
                url = self._first(
                    it, "url", "adLibraryUrl", "snapshotUrl", "link",
                    default="https://www.facebook.com/ads/library/",
                )
                ad_count = self._first(it, "totalActiveAds", "collationCount", "adCount")

                products.append(
                    Product(
                        name=str(name),
                        source=self.name,
                        url=str(url),
                        image_url=image,
                        seller=str(self._first(it, "pageName", "page_name", default=name)),
                        keyword=kw,
                        active_days=active_days,
                        ad_count=int(ad_count) if str(ad_count or "").isdigit() else None,
                        raw=it,
                    )
                )
        return products
