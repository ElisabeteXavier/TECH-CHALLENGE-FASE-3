"""Paths, variáveis de ambiente e estado do grafo."""

import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv

load_dotenv()

# --- raiz do projeto ---
BASE_DIR = Path(__file__).resolve().parent

# --- pastas de dados ---
DADOS_DIR = BASE_DIR / "dados"
JSON_DIR = DADOS_DIR / "json"
PDF_DIR = DADOS_DIR / "pdfs"
FAISS_DIR = BASE_DIR / "faiss_index"

# --- modelos ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

# --- RAG ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "300"))
RAG_K = int(os.getenv("RAG_K", "5"))
RAG_FETCH_K = int(os.getenv("RAG_FETCH_K", "20"))

# PDFs usados no RAG (mesma ordem do notebook)
PDF_NOMES = [
    "faqs.pdf",
    "protocolos.pdf",
    "receitas.pdf",
    "triagens.pdf",
    "laudos.pdf",
    "evolucoes.pdf",
]


def get_pdf_paths() -> list[str]:
    """Retorna caminhos absolutos dos PDFs em dados/pdfs/."""
    paths = []
    for nome in PDF_NOMES:
        caminho = PDF_DIR / nome
        if not caminho.is_file():
            raise FileNotFoundError(
                f"PDF não encontrado: {caminho}\n"
                "Rode antes: python gerar_dados.py"
            )
        paths.append(str(caminho))
    return paths


class MedicalState(TypedDict, total=False):
    pergunta: str
    patient_id: str
    dados_paciente: str
    alertas: list[str]
    contexto_recuperado: str
    fontes: str
    sugestao_conduta: str
    validado_por_humano: bool
    resposta: str
    historico: list


def estado_inicial(pergunta: str, historico: list | None = None, patient_id: str = "") -> MedicalState:
    """Estado padrão para nova consulta no grafo."""
    return MedicalState(
        pergunta=pergunta,
        patient_id=patient_id,
        dados_paciente="",
        alertas=[],
        contexto_recuperado="",
        fontes="",
        sugestao_conduta="",
        validado_por_humano=False,
        resposta="",
        historico=historico or [],
    )