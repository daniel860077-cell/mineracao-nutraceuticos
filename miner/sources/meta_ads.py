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
    start = item.get("start_date") or item.get("startDate") or item.get("ad_delivery_start_time")
    # start_date costuma vir como timestamp unix (segundos)
    if isinstance(start, (int, float)) or (isinstance(start, str) and start.isdigit()):
        try:
            dt = datetime.fromtimestamp(int(start), tz=timezone.utc)
            return max(0, (datetime.now(timezone.utc) - dt).days)
        except (ValueError, OSError):
            pass
    fmt_str = item.get("start_date_formatted") or (start if isinstance(start, str) else None)
    if fmt_str:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                dt = datetime.strptime(str(fmt_str)[:19], fmt[:19] if len(fmt) > 19 else fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return max(0, (datetime.now(timezone.utc) - dt).days)
            except ValueError:
                continue
    return None


def _extract_image(snap: dict) -> str | None:
    for key in ("images", "cards", "videos"):
        arr = snap.get(key) or []
        for el in arr:
            if not isinstance(el, dict):
                continue
            img = (
                el.get("original_image_url") or el.get("resized_image_url")
                or el.get("video_preview_image_url") or el.get("image_url")
            )
            if img:
                return img
    return snap.get("page_profile_picture_url")


def _clean(v) -> str | None:
    """Texto utilizável? Rejeita placeholders de anúncio dinâmico ({{...}})."""
    if isinstance(v, dict):
        v = v.get("text")
    if not v:
        return None
    s = str(v).strip()
    if not s or "{{" in s:
        return None
    return s[:120]


def _extract_name(snap: dict, fallback: str) -> str:
    candidates = []
    for key in ("title", "caption", "link_description", "body"):
        candidates.append(_clean(snap.get(key)))
    cards = snap.get("cards") or []
    if cards and isinstance(cards[0], dict):
        for key in ("title", "link_description", "body"):
            candidates.append(_clean(cards[0].get(key)))
    for c in candidates:
        if c:
            return c
    return fallback


class MetaAdsSource(Source):
    """Meta Ad Library. Validação = tempo de veiculação (anúncio ativo
    há > min_active_days) e quantidade de anúncios idênticos por página."""

    name = "meta_ads"

    def collect(self, keywords: List[str]) -> List[Product]:
        actor = self.cfg["actor_id"]
        min_days = int(self.cfg.get("min_active_days", 5))
        cap = max(10, int(self.cfg.get("count_per_keyword", 30)))  # actor exige >= 10
        country = self.g.get("country", "BR")
        products: List[Product] = []

        for kw in keywords:
            run_input = {
                "urls": [{"url": _ad_library_url(kw, country)}],
                "count": cap,
                "scrapePageAds.activeStatus": "active",
                "scrapePageAds.countryCode": country,
            }
            try:
                items = self.runner.run(actor, run_input)
            except Exception as exc:  # noqa: BLE001
                log.warning("Meta falhou para '%s': %s", kw, exc)
                continue

            for it in items:
                if it.get("error"):
                    log.warning("Meta retornou erro: %s", it["error"])
                    continue
                active_days = _parse_days_active(it)
                if active_days is not None and active_days < min_days:
                    continue

                snap = it.get("snapshot") or {}
                page_name = self._first(it, "page_name", "pageName", default=kw)
                name = _extract_name(snap, str(page_name))
                ad_count = self._first(it, "collation_count", "ads_count", "total")
                url = self._first(it, "ad_library_url", "url", default=_ad_library_url(kw, country))

                products.append(
                    Product(
                        name=name,
                        source=self.name,
                        url=str(url),
                        image_url=_extract_image(snap),
                        seller=str(page_name),
                        keyword=kw,
                        active_days=active_days,
                        ad_count=int(ad_count) if str(ad_count or "").isdigit() else None,
                        raw={"page_id": it.get("page_id"), "ad_archive_id": it.get("ad_archive_id")},
                    )
                )
        return products
