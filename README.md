# 🏥 Assistente Médico Inteligente — Tech Challenge Fase 3

Assistente virtual para apoiar condutas clínicas com base em protocolos hospitalares, usando LangChain, LangGraph e RAG.

O sistema **não substitui o médico** — inclui validação humana das respostas.

---

# 📂 Estrutura do projeto

```text
TECH-CHALLENGE-FASE-3/
├── README.md
├── requirements.txt
├── .env.example
├── gerar_dados.py           # gera JSON + PDF (dados hospitalares)
│
├── dados/
│   ├── json/                # FAQs, protocolos, laudos, receitas...
│   ├── pdfs/                # PDFs para o RAG
│   └── prontuario_exemplo.json
│
├── notebooks/
│   ├── gerar_dados.ipynb    # versão notebook (legado)
│   ├── multi-agentes.ipynb  # assistente (RAG + LangGraph)
│   └── eda.ipynb            # fine-tuning PubMedQA (colega do grupo)
│
├── config.py                # paths e variáveis (a implementar)
├── rag.py
├── agentes.py
├── grafo.py
└── main.py
```

---

# 🚀 Instalação

```bash
git clone <url-do-repositorio>
cd TECH-CHALLENGE-FASE-3

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

Edite o `.env` e preencha:

```env
OPENAI_API_KEY=sua_chave
```

> A chave da OpenAI é necessária apenas para gerar novos JSON pela API.

---

# 📊 Gerar dados (`gerar_dados.py`)

Script responsável por preparar os dados hospitalares sintéticos em:

- JSON
- PDF

Os PDFs são usados posteriormente no pipeline RAG.

---

# ⚙️ Comportamento do script

| Situação | O que acontece |
|---|---|
| JSON já existe em `dados/json/` | Usa o arquivo local e gera o PDF |
| JSON não existe | Chama a OpenAI, salva JSON e gera PDF |
| `--apenas-pdf` | Só gera PDFs a partir dos JSON |
| `--force` | Regera tudo via OpenAI |

---

# 📁 Categorias geradas

- faqs
- protocolos
- laudos
- receitas
- triagens
- evolucoes

---

# ▶️ Uso

## Gerar PDFs a partir dos JSON existentes

```bash
python gerar_dados.py
```

ou explicitamente:

```bash
python gerar_dados.py --apenas-pdf
```

---

## Regerar JSON + PDF pela OpenAI

```bash
python gerar_dados.py --force
```

---

# 🔐 Variáveis de ambiente (`.env`)

```env
OPENAI_API_KEY=sua_chave
OPENAI_MODEL=gpt-4o-mini
```

| Variável | Obrigatória |
|---|---|
| OPENAI_API_KEY | apenas se gerar JSON novo |
| OPENAI_MODEL | opcional |

---

# 📦 Saída esperada

```text
dados/json/faqs.json
dados/pdfs/faqs.pdf

dados/json/protocolos.json
dados/pdfs/protocolos.pdf

dados/json/laudos.json
dados/pdfs/laudos.pdf
```

---

# 🤖 Assistente médico (em desenvolvimento)

A lógica principal do assistente está atualmente em:

```text
notebooks/multi-agentes.ipynb
```

Tecnologias utilizadas:

- LangChain
- LangGraph
- FAISS
- RAG
- validação humana

---

# 🧭 Ordem sugerida de execução

## 1. Gerar PDFs

```bash
python gerar_dados.py
```

---

## 2. Testar o assistente

Abrir:

```text
notebooks/multi-agentes.ipynb
```

Pode ser executado:
- localmente
- Google Colab

---

## 3. Fine-tuning

Notebook:

```text
notebooks/eda.ipynb
```

Responsável:
- integrante do grupo

---

# 🧩 Módulos Python

| Arquivo | Responsabilidade |
|---|---|
| `gerar_dados.py` | geração de JSON e PDFs |
| `config.py` | paths e configurações |
| `rag.py` | embeddings, FAISS e retriever |
| `agentes.py` | pesquisador, analista e validador |
| `grafo.py` | fluxo LangGraph |
| `main.py` | CLI do assistente |

---

# 🎯 Objetivos do Tech Challenge

- Fine-tuning com dados médicos
- Assistente baseado em protocolos internos
- Segurança e validação humana
- Uso de RAG para apoio clínico
- Código modular em Python
- Documentação via README

---

# 🧰 Tecnologias

- Python
- OpenAI
- ReportLab
- LangChain
- LangGraph
- Hugging Face
- FAISS
- Pandas

---