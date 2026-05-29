from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List

from .models import Product

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "mineracao.db"


class Store:
    """Persistência leve em SQLite p/ deduplicação na janela de N dias."""

    def __init__(self, path: Path | str = DB_PATH):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS delivered (
                fingerprint TEXT PRIMARY KEY,
                name        TEXT,
                source      TEXT,
                url         TEXT,
                seller      TEXT,
                score       REAL,
                delivered_at TEXT
            )
            """
        )
        self.conn.commit()

    def recently_delivered(self, window_days: int) -> set[str]:
        cutoff = (datetime.utcnow() - timedelta(days=window_days)).isoformat()
        rows = self.conn.execute(
            "SELECT fingerprint FROM delivered WHERE delivered_at >= ?", (cutoff,)
        ).fetchall()
        return {r["fingerprint"] for r in rows}

    def filter_new(self, products: Iterable[Product], window_days: int) -> List[Product]:
        seen = self.recently_delivered(window_days)
        out, batch_seen = [], set()
        for p in products:
            fp = p.fingerprint
            if fp in seen or fp in batch_seen:
                continue
            batch_seen.add(fp)
            out.append(p)
        return out

    def mark_delivered(self, products: Iterable[Product]) -> None:
        now = datetime.utcnow().isoformat()
        self.conn.executemany(
            """
            INSERT OR REPLACE INTO delivered
                (fingerprint, name, source, url, seller, score, delivered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (p.fingerprint, p.name, p.source, p.url, p.seller, p.score, now)
                for p in products
            ],
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
