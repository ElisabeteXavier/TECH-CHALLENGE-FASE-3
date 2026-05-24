"""Logging estruturado para auditoria clínica (HITL + RAG)."""

import json
from datetime import datetime, timezone
from pathlib import Path

from config import DADOS_DIR

LOG_DIR = DADOS_DIR / "logs"


def registrar_auditoria(evento: dict) -> Path:
    """Append de evento em JSONL (dados/logs/auditoria.jsonl)."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / "auditoria.jsonl"
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **evento,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return path
