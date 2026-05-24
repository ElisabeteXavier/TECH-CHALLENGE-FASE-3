"""Embeddings, índice FAISS e retriever."""

import shutil
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    FAISS_DIR,
    JSON_DIR,
    RAG_FETCH_K,
    RAG_K,
    RAG_SEARCH_TYPE,
    get_pdf_paths,
)

_retriever = None


def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": EMBEDDING_DEVICE},
        encode_kwargs={"normalize_embeddings": True},
    )


def _indice_persistido_existe() -> bool:
    """Verifica se o índice FAISS foi salvo em disco."""
    return (
        FAISS_DIR.is_dir()
        and (FAISS_DIR / "index.faiss").is_file()
        and (FAISS_DIR / "index.pkl").is_file()
    )


def _retriever_from_vectorstore(vectorstore: FAISS):
    """Retriever configurável via RAG_SEARCH_TYPE (mmr ou similarity)."""
    if RAG_SEARCH_TYPE == "similarity":
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": RAG_K},
        )
    fetch_k = max(RAG_K, RAG_FETCH_K)
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": RAG_K, "fetch_k": fetch_k},
    )


def _categoria_de_arquivo(caminho: str) -> str:
    """Nome do PDF sem extensão (faqs, protocolos, laudos, ...)."""
    return Path(caminho).stem


def _pagina_do_documento(metadata: dict) -> int:
    """PyPDFLoader usa 'page' (0-based); expõe página humana (1-based)."""
    pagina = metadata.get("page", metadata.get("page_number"))
    if pagina is None:
        return 0
    return int(pagina) + 1


def _tipo_fonte_para_caminho(caminho: str) -> tuple[str, str | None]:
    """
    Padroniza tipo_fonte no pipeline JSON -> PDF -> RAG.
    PDF indexado: tipo_fonte=pdf; se existir JSON da mesma categoria, registra par.
    """
    categoria = _categoria_de_arquivo(caminho)
    json_path = JSON_DIR / f"{categoria}.json"
    if json_path.is_file():
        return "pdf", json_path.name
    return "pdf", None


def _enriquecer_metadata_pagina(doc, caminho: str) -> None:
    path = Path(caminho)
    categoria = _categoria_de_arquivo(caminho)
    tipo_fonte, json_par = _tipo_fonte_para_caminho(caminho)
    doc.metadata["fonte_arquivo"] = path.name
    doc.metadata["categoria"] = categoria
    doc.metadata["pagina"] = _pagina_do_documento(doc.metadata)
    doc.metadata["tipo_fonte"] = tipo_fonte
    if json_par:
        doc.metadata["json_origem"] = json_par
    # Compatibilidade com código e índices antigos
    doc.metadata["fonte"] = str(path.resolve())
    doc.metadata["tipo"] = "documento_medico"


def _atribuir_chunk_ids(chunks: list) -> list:
    """Identificador estável por categoria após o split."""
    contadores: dict[str, int] = {}
    for doc in chunks:
        categoria = doc.metadata.get("categoria", "doc")
        indice = contadores.get(categoria, 0)
        doc.metadata["chunk_id"] = f"{categoria}_{indice:04d}"
        contadores[categoria] = indice + 1
    return chunks


CABECALHO_FONTES_PADRAO = "arquivo | categoria | pagina | chunk_id | tipo_fonte"


def formatar_fonte_metadata(metadata: dict) -> str:
    """Linha legível para HITL, resposta final e log."""
    arquivo = metadata.get("fonte_arquivo") or Path(
        str(metadata.get("fonte", "desconhecida"))
    ).name
    tipo = metadata.get("tipo_fonte", "?")
    if metadata.get("json_origem"):
        tipo = f"{tipo}+json"
    return (
        f"{arquivo} | "
        f"{metadata.get('categoria', '?')} | "
        f"p.{metadata.get('pagina', '?')} | "
        f"{metadata.get('chunk_id', '?')} | "
        f"{tipo}"
    )


def registro_fonte_de_metadata(metadata: dict) -> dict:
    """Registro estruturado para auditoria JSONL."""
    arquivo = metadata.get("fonte_arquivo") or Path(
        str(metadata.get("fonte", "desconhecida"))
    ).name
    tipo_fonte = metadata.get("tipo_fonte", "")
    json_origem = metadata.get("json_origem")
    return {
        "fonte_arquivo": arquivo,
        "categoria": metadata.get("categoria", ""),
        "pagina": metadata.get("pagina", 0),
        "chunk_id": metadata.get("chunk_id", ""),
        "tipo_fonte": tipo_fonte,
        "json_origem": json_origem or "",
        "linha": formatar_fonte_metadata(metadata),
    }


def _chave_fonte(metadata: dict) -> str:
    """Chave única por chunk recuperado (deduplicação)."""
    registro = registro_fonte_de_metadata(metadata)
    return (
        f"{registro['fonte_arquivo']}|{registro['categoria']}|"
        f"{registro['pagina']}|{registro['chunk_id']}"
    )


def montar_fontes_rag(documentos: list) -> tuple[str, list[dict]]:
    """
    Monta bloco de fontes sem duplicatas, ordenado e padronizado.
    Retorna (texto para exibição, lista estruturada para log).
    """
    vistos: set[str] = set()
    registros: list[dict] = []

    for doc in documentos:
        chave = _chave_fonte(doc.metadata)
        if chave in vistos:
            continue
        vistos.add(chave)
        registros.append(registro_fonte_de_metadata(doc.metadata))

    registros.sort(
        key=lambda r: (
            r.get("categoria", ""),
            r.get("fonte_arquivo", ""),
            r.get("pagina", 0),
            r.get("chunk_id", ""),
        )
    )

    if not registros:
        return "Nenhuma fonte recuperada.", []

    linhas = [f"- {r['linha']}" for r in registros]
    texto = f"{CABECALHO_FONTES_PADRAO}\n" + "\n".join(linhas)
    return texto, registros


def _carregar_documentos(caminhos_pdfs: list[str]):
    documentos_totais = []
    for caminho in caminhos_pdfs:
        loader = PyPDFLoader(caminho)
        documentos = loader.load()
        for doc in documentos:
            _enriquecer_metadata_pagina(doc, caminho)
        documentos_totais.extend(documentos)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documentos_totais)
    return _atribuir_chunk_ids(chunks)


def _criar_e_salvar_vectorstore(caminhos_pdfs: list[str]) -> FAISS:
    embedding_model = get_embeddings()
    docs = _carregar_documentos(caminhos_pdfs)
    vectorstore = FAISS.from_documents(docs, embedding_model)
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(FAISS_DIR))
    print(f"Índice FAISS criado e salvo em {FAISS_DIR}")
    return vectorstore


def _carregar_vectorstore() -> FAISS:
    embedding_model = get_embeddings()
    vectorstore = FAISS.load_local(
        str(FAISS_DIR),
        embedding_model,
        allow_dangerous_deserialization=True,
    )
    print(f"Índice FAISS carregado de {FAISS_DIR}")
    return vectorstore


def configurar_base_conhecimento(caminhos_pdfs: list[str]):
    if _indice_persistido_existe():
        vectorstore = _carregar_vectorstore()
    else:
        print("Índice FAISS não encontrado. Indexando PDFs...")
        vectorstore = _criar_e_salvar_vectorstore(caminhos_pdfs)
    return _retriever_from_vectorstore(vectorstore)


def estatisticas_indice(caminhos_pdfs: list[str] | None = None) -> dict:
    """Conta PDFs, chunks e vetores persistidos (sem alterar o índice)."""
    caminhos = caminhos_pdfs or get_pdf_paths()
    chunks = _carregar_documentos(caminhos)

    por_categoria: dict[str, int] = {}
    com_json_origem = 0
    for chunk in chunks:
        cat = chunk.metadata.get("categoria", "desconhecida")
        por_categoria[cat] = por_categoria.get(cat, 0) + 1
        if chunk.metadata.get("json_origem"):
            com_json_origem += 1

    vetores = 0
    indice_existe = _indice_persistido_existe()
    if indice_existe:
        vetores = int(_carregar_vectorstore().index.ntotal)

    return {
        "indice_persistido": indice_existe,
        "diretorio_indice": str(FAISS_DIR),
        "pdfs_indexados": len(caminhos),
        "chunks_apos_split": len(chunks),
        "vetores_no_faiss": vetores,
        "chunks_com_json_origem": com_json_origem,
        "por_categoria": por_categoria,
        "embedding_model": EMBEDDING_MODEL,
        "rag_search_type": RAG_SEARCH_TYPE,
        "rag_k": RAG_K,
        "rag_fetch_k": RAG_FETCH_K,
    }


def rebuild_faiss_index(force: bool = False) -> bool:
    """
    Recria o índice FAISS. Com force=True remove faiss_index/ antes.
    Retorna True se houve rebuild, False se manteve índice existente.
    """
    global _retriever
    _retriever = None

    if force and FAISS_DIR.exists():
        shutil.rmtree(FAISS_DIR)
        print(f"Índice removido: {FAISS_DIR}")

    if force or not _indice_persistido_existe():
        _criar_e_salvar_vectorstore(get_pdf_paths())
        _retriever = None
        return True

    print(f"Índice já existe em {FAISS_DIR}. Use --force para recriar.")
    return False


def build_retriever():
    """Carrega ou cria o índice FAISS a partir dos PDFs em dados/pdfs/."""
    global _retriever
    _retriever = configurar_base_conhecimento(get_pdf_paths())
    return _retriever


def get_retriever():
    """Retorna o retriever; cria na primeira chamada."""
    global _retriever
    if _retriever is None:
        build_retriever()
    return _retriever