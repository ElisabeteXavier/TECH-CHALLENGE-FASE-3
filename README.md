# 🏥 Assistente Médico Inteligente — Tech Challenge Fase 3

Assistente virtual para apoiar condutas clínicas com base em protocolos hospitalares, usando LangChain / LangGraph e RAG.

O sistema **não substitui o médico** — inclui validação humana das respostas.

---

## 📂 Estrutura do projeto (simples)

```text
TECH-CHALLENGE-FASE-3/
├── README.md
├── requirements.txt
├── .env.example
│
├── dados/
│   ├── json/                  # FAQs, protocolos, laudos, receitas...
│   ├── pdfs/                  # PDFs para o RAG (gerados no notebook)
│   └── prontuario_exemplo.json
│
├── notebooks/
│   ├── gerar_dados.ipynb      # gera JSON e PDFs
│   ├── multi-agentes.ipynb    # assistente (RAG + LangGraph)
│   └── eda.ipynb              # fine-tuning (PubMedQA)
│
├── config.py                  # paths e variáveis de ambiente
├── rag.py                     # embeddings + índice + busca
├── agentes.py                 # pesquisador, analista, validador
├── grafo.py                   # monta o fluxo LangGraph
└── main.py                    # entrada: python main.py
```

Os arquivos `.py` na raiz estão vazios por enquanto — a lógica atual está em `notebooks/multi-agentes.ipynb`. Migre para os `.py` quando quiser rodar pelo terminal.

---

## 🚀 Como usar (por enquanto)

1. Crie o ambiente e instale dependências (veja `requirements.txt` quando preenchido).
2. Copie `.env.example` para `.env` e coloque sua `OPENAI_API_KEY`.
3. Rode os notebooks na ordem:
   - `gerar_dados.ipynb` → gera dados em `dados/json` e `dados/pdfs`
   - `multi-agentes.ipynb` → assistente principal
   - `eda.ipynb` → fine-tuning (responsável do grupo)

---

## 🧩 O que cada arquivo Python vai fazer

| Arquivo | Função |
|---------|--------|
| `config.py` | Caminhos (`dados/json`, `dados/pdfs`) e configurações |
| `rag.py` | Carregar PDFs, criar FAISS, retriever |
| `agentes.py` | Nós do grafo (pesquisa, análise, validação humana) |
| `grafo.py` | Definir e compilar o LangGraph |
| `main.py` | Executar uma consulta |

---

## 🎯 Objetivos do challenge

- Fine-tuning com dados médicos (notebook `eda.ipynb` + colega do grupo)
- Assistente com LangChain e dados do hospital
- Segurança: não prescrever sem validação; citar fontes
- Código modular em Python + README

---

## 🧰 Tecnologias

Python · LangChain · LangGraph · OpenAI (temporário) · Hugging Face · FAISS
