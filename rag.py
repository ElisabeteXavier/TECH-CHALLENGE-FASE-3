"""Embeddings, índice FAISS e retriever."""

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
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


def configurar_base_conhecimento(caminhos_pdfs: list[str]):
    embedding_model = get_embeddings()
    documentos_totais = []

    for caminho in caminhos_pdfs:
        loader = PyPDFLoader(caminho)
        documentos = loader.load()
        for doc in documentos:
            doc.metadata["fonte"] = caminho
            doc.metadata["tipo"] = "documento_medico"
        documentos_totais.extend(documentos)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    docs = splitter.split_documents(documentos_totais)

    vectorstore = FAISS.from_documents(docs, embedding_model)
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": RAG_K, "fetch_k": RAG_FETCH_K},
    )


def build_retriever():
    """Cria o índice FAISS a partir dos PDFs em dados/pdfs/."""
    global _retriever
    _retriever = configurar_base_conhecimento(get_pdf_paths())
    return _retriever


def get_retriever():
    """Retorna o retriever; cria na primeira chamada."""
    global _retriever
    if _retriever is None:
        build_retriever()
    return _retriever