"""
Rebuild e diagnóstico do índice FAISS do RAG.

Uso:
  python rebuild_rag_index.py --stats
  python rebuild_rag_index.py --force
  python rebuild_rag_index.py --force --stats
"""

from __future__ import annotations

import argparse
import sys
import time

from rag import estatisticas_indice, rebuild_faiss_index


def _imprimir_stats(stats: dict) -> None:
    print("\n=== Estatísticas do índice RAG ===")
    print(f"Diretório:           {stats['diretorio_indice']}")
    print(f"Índice persistido:   {'sim' if stats['indice_persistido'] else 'não'}")
    print(f"PDFs:                {stats['pdfs_indexados']}")
    print(f"Chunks (após split): {stats['chunks_apos_split']}")
    print(f"Vetores no FAISS:    {stats['vetores_no_faiss']}")
    print(f"Chunks com JSON par: {stats['chunks_com_json_origem']}")
    if "chunks_com_subcategoria" in stats:
        print(f"Chunks com subcategoria: {stats['chunks_com_subcategoria']}")
    print(f"Embedding:           {stats['embedding_model']}")
    print(f"Busca:               {stats['rag_search_type']} (k={stats['rag_k']}, fetch_k={stats['rag_fetch_k']})")
    print("\nChunks por categoria:")
    for categoria, total in sorted(stats["por_categoria"].items()):
        print(f"  - {categoria}: {total}")
    if stats["indice_persistido"] and stats["vetores_no_faiss"] != stats["chunks_apos_split"]:
        print(
            "\nAviso: vetores no FAISS diferem dos chunks atuais — "
            "rode com --force para reindexar."
        )
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild/diagnóstico do índice FAISS (RAG)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove faiss_index/ e recria o índice a partir dos PDFs",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Exibe estatísticas (PDFs, chunks, vetores, categorias)",
    )
    args = parser.parse_args()

    if not args.force and not args.stats:
        parser.print_help()
        print("\nExemplo: python rebuild_rag_index.py --force --stats")
        return 1

    if args.force:
        t0 = time.perf_counter()
        rebuild_faiss_index(force=True)
        print(f"Rebuild concluído em {time.perf_counter() - t0:.1f}s")

    if args.stats:
        stats = estatisticas_indice()
        _imprimir_stats(stats)

    return 0


if __name__ == "__main__":
    sys.exit(main())
