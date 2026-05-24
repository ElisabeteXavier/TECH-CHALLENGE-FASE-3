"""Consulta a prontuários estruturados (JSON)."""

import json
from pathlib import Path

from config import DADOS_DIR, MedicalState

PRONTUARIO_PATH = DADOS_DIR / "prontuario_exemplo.json"


def _carregar_prontuarios() -> dict:
    if not PRONTUARIO_PATH.is_file():
        return {}
    with open(PRONTUARIO_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {p["paciente_id"]: p for p in data if "paciente_id" in p}
    if "paciente_id" in data:
        return {data["paciente_id"]: data}
    return {}


def obter_resumo_paciente(patient_id: str) -> tuple[str, list[str]]:
    """Retorna texto formatado e lista de alertas clínicos."""
    pacientes = _carregar_prontuarios()
    paciente = pacientes.get(patient_id)
    if not paciente:
        return "", [f"Paciente '{patient_id}' não encontrado no prontuário."]

    alertas: list[str] = []
    exames = paciente.get("exames_pendentes") or []
    if exames:
        alertas.append(f"Exames pendentes: {', '.join(exames)}")

    alergias = paciente.get("alergias") or []
    if alergias:
        alertas.append(f"Alergias registradas: {', '.join(alergias)}")

    sinais = paciente.get("sinais_vitais") or {}
    if sinais.get("spo2") is not None and sinais["spo2"] < 92:
        alertas.append(f"Alerta: SpO2 baixa ({sinais['spo2']}%)")

    linhas = [
        f"ID: {paciente.get('paciente_id', patient_id)}",
        f"Nome: {paciente.get('nome', 'N/A')}",
        f"Idade: {paciente.get('idade', 'N/A')}",
        f"Alergias: {', '.join(alergias) or 'Nenhuma registrada'}",
        f"Medicamentos em uso: {', '.join(paciente.get('medicamentos_em_uso') or []) or 'Nenhum'}",
        f"Exames pendentes: {', '.join(exames) or 'Nenhum'}",
    ]
    if sinais:
        linhas.append(f"Sinais vitais: {sinais}")

    return "\n".join(linhas), alertas


def carregar_prontuario(state: MedicalState) -> dict:
    """Nó LangGraph: injeta dados estruturados do paciente no estado."""
    patient_id = (state.get("patient_id") or "").strip()
    if not patient_id:
        return {"dados_paciente": "", "alertas": []}

    resumo, alertas = obter_resumo_paciente(patient_id)
    return {"dados_paciente": resumo, "alertas": alertas}
