#!/usr/bin/env python3
"""Entrypoint do cron diário de mineração de nutracêuticos.

Uso:
    python run_daily.py            # coleta, deduplica, pontua e ENVIA
    python run_daily.py --dry-run  # faz tudo menos enviar; imprime o resultado
"""
from __future__ import annotations

import argparse
import logging
import sys

from miner.config import load_config
from miner.pipeline import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Bot de mineração de nutracêuticos")
    parser.add_argument("--config", default=None, help="Caminho do config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Não envia; só imprime")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        cfg = load_config(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO de configuração: {exc}", file=sys.stderr)
        return 2

    products = run(cfg, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n=== {len(products)} produtos selecionados (dry-run) ===")
        for i, p in enumerate(products, 1):
            print(f"{i}. [{p.source}] {p.name}  | {p.traction_label} | score {p.score}")
            print(f"   {p.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
