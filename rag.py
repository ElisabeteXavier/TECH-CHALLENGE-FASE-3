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


def _carregar_documentos(caminhos_pdfs: list[str]):
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
    return splitter.split_documents(documentos_totais)


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