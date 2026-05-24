"""
Avaliação básica hit@k do retriever RAG.

Uso:
  python avaliar_rag_hitk.py
  python avaliar_rag_hitk.py --k 3 5
  python avaliar_rag_hitk.py --casos dados/externos/docs/rag_hitk_casos.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import RAG_K, RAG_SEARCH_TYPE
from rag import build_retriever

BASE_DIR = Path(__file__).resolve().parent
CASOS_PADRAO = BASE_DIR / "dados" / "externos" / "docs" / "rag_hitk_casos.json"
SAIDA_PADRAO = BASE_DIR / "dados" / "externos" / "docs" / "rag_hitk_resultados.json"


def carregar_casos(caminho: Path) -> list[dict]:
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    if not isinstance(dados, list) or not dados:
        raise ValueError(f"Arquivo de casos inválido ou vazio: {caminho}")
    return dados


def categorias_recuperadas(documentos: list, limite: int) -> list[str]:
    cats = []
    for doc in documentos[:limite]:
        cat = (doc.metadata or {}).get("categoria", "")
        if cat:
            cats.append(str(cat))
    return cats


def hit_no_top_k(categorias: list[str], esperada: str, k: int) -> bool:
    esperada = esperada.strip().lower()
    top = [c.lower() for c in categorias[:k]]
    return esperada in top


def avaliar_casos(
    casos: list[dict],
    retriever,
    valores_k: list[int],
) -> dict:
    resultados_casos = []
    acertos_por_k = {k: 0 for k in valores_k}

    for caso in casos:
        pergunta = caso["pergunta"]
        esperada = caso["categoria_esperada"]
        docs = retriever.invoke(pergunta)
        cats = categorias_recuperadas(docs, max(valores_k))

        linha = {
            "id": caso.get("id", ""),
            "pergunta": pergunta,
            "categoria_esperada": esperada,
            "categorias_top": cats[: max(valores_k)],
            "hits": {},
        }
        for k in valores_k:
            acertou = hit_no_top_k(cats, esperada, k)
            linha["hits"][f"hit@{k}"] = acertou
            if acertou:
                acertos_por_k[k] += 1
        resultados_casos.append(linha)

    total = len(casos)
    metricas = {
        f"hit@{k}": round(acertos_por_k[k] / total, 4) if total else 0.0
        for k in valores_k
    }
    return {
        "total_casos": total,
        "metricas": metricas,
        "casos": resultados_casos,
    }


def imprimir_relatorio(relatorio: dict, valores_k: list[int]) -> None:
    print("\n=== Avaliação RAG — hit@k ===")
    print(f"Casos avaliados: {relatorio['total_casos']}")
    for k in valores_k:
        chave = f"hit@{k}"
        valor = relatorio["metricas"][chave]
        print(f"  {chave}: {valor:.2%}")
    print("\nDetalhe por caso:")
    for caso in relatorio["casos"]:
        hits = ", ".join(
            f"{h}={'sim' if v else 'não'}" for h, v in caso["hits"].items()
        )
        print(f"  [{caso['id']}] esperado={caso['categoria_esperada']} | {hits}")
        print(f"       top: {caso['categorias_top']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Avalia hit@k do retriever RAG")
    parser.add_argument(
        "--casos",
        type=Path,
        default=CASOS_PADRAO,
        help="JSON com lista de casos (pergunta + categoria_esperada)",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=SAIDA_PADRAO,
        help="Arquivo JSON de saída com métricas e detalhes",
    )
    parser.add_argument(
        "--k",
        type=int,
        nargs="+",
        default=None,
        help="Valores de k para hit@k (padrão: RAG_K do .env)",
    )
    args = parser.parse_args()

    valores_k = sorted(set(args.k or [RAG_K]))
    if any(v < 1 for v in valores_k):
        print("Erro: k deve ser >= 1", file=sys.stderr)
        return 1

    casos = carregar_casos(args.casos)
    print(f"Carregando retriever ({len(casos)} casos, k={valores_k})...")
    retriever = build_retriever()

    relatorio = avaliar_casos(casos, retriever, valores_k)
    relatorio["gerado_em"] = datetime.now(timezone.utc).isoformat()
    try:
        arquivo_casos_rel = args.casos.resolve().relative_to(BASE_DIR)
    except ValueError:
        arquivo_casos_rel = args.casos

    relatorio["config"] = {
        "rag_k": RAG_K,
        "rag_search_type": RAG_SEARCH_TYPE,
        "arquivo_casos": str(arquivo_casos_rel),
    }

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)

    imprimir_relatorio(relatorio, valores_k)
    print(f"Resultados salvos em: {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
