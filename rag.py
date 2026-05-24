"""Embeddings, índice FAISS e retriever."""

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
    RAG_FETCH_K,
    RAG_K,
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
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": RAG_K, "fetch_k": RAG_FETCH_K},
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


def _enriquecer_metadata_pagina(doc, caminho: str) -> None:
    path = Path(caminho)
    categoria = _categoria_de_arquivo(caminho)
    doc.metadata["fonte_arquivo"] = path.name
    doc.metadata["categoria"] = categoria
    doc.metadata["pagina"] = _pagina_do_documento(doc.metadata)
    doc.metadata["tipo_fonte"] = "pdf"
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


def formatar_fonte_metadata(metadata: dict) -> str:
    """Linha legível para HITL e resposta final."""
    return (
        f"{metadata.get('fonte_arquivo', metadata.get('fonte', 'desconhecida'))} | "
        f"{metadata.get('categoria', '?')} | "
        f"p.{metadata.get('pagina', '?')} | "
        f"{metadata.get('chunk_id', '?')}"
    )


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