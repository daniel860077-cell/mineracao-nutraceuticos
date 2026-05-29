from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple

import requests

log = logging.getLogger("miner.tg_commands")

HELP = (
    "🤖 <b>Bot de Mineração</b>\n\n"
    "Comandos:\n"
    "• <code>/buscar termo1, termo2, termo3</code> — define o nicho/categoria a pesquisar "
    "(qualquer nicho: nutracêuticos, eletrônicos, moda...).\n"
    "• <code>/status</code> — mostra o nicho atual.\n"
    "• <code>/ajuda</code> — esta mensagem.\n\n"
    "Depois de definir, o bot passa a minerar esses termos na próxima execução "
    "e te envia os 5-6 produtos validados do dia."
)


def _api(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


def _send(token: str, chat_id: str, text: str) -> None:
    try:
        requests.post(
            _api(token, "sendMessage"),
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=30,
        )
    except requests.RequestException as exc:
        log.warning("Falha ao responder no Telegram: %s", exc)


def _parse_keywords(raw: str) -> List[str]:
    parts = re.split(r"[,\n;]+", raw)
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return out


def register_commands(token: str) -> None:
    """Mostra os comandos no menu do Telegram (one-shot, idempotente)."""
    try:
        requests.post(_api(token, "setMyCommands"), json={"commands": [
            {"command": "buscar", "description": "Definir o nicho/categoria a pesquisar"},
            {"command": "status", "description": "Ver o nicho atual"},
            {"command": "ajuda", "description": "Como usar o bot"},
        ]}, timeout=30)
    except requests.RequestException:
        pass


def process_commands(secrets: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Lê novas mensagens do bot e aplica comandos. Atualiza `state` in-place.
    Retorna (state, changed) — changed=True se o nicho ou o offset mudaram."""
    token = secrets.get("telegram_bot_token")
    chat_id = secrets.get("telegram_chat_id")
    if not token:
        return state, False

    offset = int(state.get("telegram_offset", 0))
    try:
        r = requests.get(
            _api(token, "getUpdates"),
            params={"offset": offset + 1, "timeout": 0, "allowed_updates": '["message"]'},
            timeout=30,
        )
        updates = r.json().get("result", [])
    except (requests.RequestException, ValueError) as exc:
        log.warning("getUpdates falhou: %s", exc)
        return state, False

    changed = False
    for up in updates:
        state["telegram_offset"] = up["update_id"]
        changed = True
        msg = up.get("message") or {}
        text = (msg.get("text") or "").strip()
        sender_chat = str((msg.get("chat") or {}).get("id", ""))
        reply_to = sender_chat or chat_id
        if not text:
            continue

        low = text.lower()
        if low.startswith(("/buscar", "/nicho", "/categoria")):
            raw = re.sub(r"^/\w+(@\w+)?\s*", "", text)
            kws = _parse_keywords(raw)
            if not kws:
                _send(token, reply_to,
                      "Use assim: <code>/buscar colágeno, emagrecedor, creatina</code>")
            else:
                state["keywords"] = kws
                _send(token, reply_to,
                      "✅ Nicho atualizado! Vou minerar:\n• " + "\n• ".join(kws) +
                      "\n\nVocê recebe os produtos validados na próxima execução.")
        elif low.startswith("/status"):
            kws = state.get("keywords") or []
            if kws:
                _send(token, reply_to, "🔎 Nicho atual:\n• " + "\n• ".join(kws))
            else:
                _send(token, reply_to,
                      "Nenhum nicho definido ainda — usando a lista padrão. "
                      "Defina com <code>/buscar ...</code>")
        elif low.startswith(("/ajuda", "/start", "/help")):
            _send(token, reply_to, HELP)

    return state, changed
