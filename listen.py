#!/usr/bin/env python3
"""Escutador leve de comandos do Telegram.

Roda com frequência (a cada ~30 min via GitHub Actions) só para captar
comandos como /buscar e confirmar rápido — SEM rodar a mineração (não gasta
créditos da Apify). O nicho escolhido fica salvo em data/state.json e é usado
pela próxima execução de run_daily.py.
"""
from __future__ import annotations

import logging
import sys

from miner.config import load_config
from miner.state import load_state, save_state
from miner.telegram_commands import process_commands, register_commands


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s | %(message)s")
    try:
        cfg = load_config()
    except Exception as exc:  # noqa: BLE001
        print(f"ERRO de configuração: {exc}", file=sys.stderr)
        return 2

    secrets = cfg["secrets"]
    register_commands(secrets.get("telegram_bot_token", ""))

    state = load_state()
    state, changed = process_commands(secrets, state)
    if changed:
        save_state(state)
        print("Estado atualizado:", state.get("keywords"))
    else:
        print("Nenhum comando novo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
