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

Edite o `.env` (a partir de `.env.example`) e preencha pelo menos:

```env
OPENAI_API_KEY=sua_chave_valida
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

> `OPENAI_API_KEY` é obrigatória para rodar `main.py` (agentes analista/validador).  
> Use `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2` em desenvolvimento local para evitar download pesado do `bge-m3`.

---

# 📊 Gerar dados (`gerar_dados.py`)

Script responsável por preparar os dados hospitalares sintéticos em:

- JSON
- PDF

Os PDFs são usados posteriormente no pipeline RAG.

---

# ⬇️ Baixar dados externos (fine-tuning/avaliação)

Para facilitar o uso por qualquer usuário, existe um comando único para baixar datasets externos em `dados/externos/`.

```bash
python baixar_dados_externos.py --dataset all
```

Opções úteis:

```bash
python baixar_dados_externos.py --dataset medquad
python baixar_dados_externos.py --dataset pubmedqa
python baixar_dados_externos.py --dataset medmcqa
python baixar_dados_externos.py --dataset all --force
```

Arquivos de saída:

- `dados/externos/raw/medquad.zip`
- `dados/externos/raw/pubmedqa_ori_pqal.json`
- `dados/externos/raw/medmcqa/*.jsonl` (quando `datasets` estiver instalado)
- `dados/externos/raw/download_manifest.json` (status e auditoria do download)

> Observação: para baixar `medmcqa`, pode ser necessário instalar dependência opcional:
>
> ```bash
> pip install datasets
> ```

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
OPENAI_API_KEY=sua_chave_valida
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
RAG_K=5
RAG_FETCH_K=20
```

| Variável | Obrigatória | Uso |
|---|---|---|
| `OPENAI_API_KEY` | sim (`main.py`) | Agentes LLM no LangGraph |
| `LLM_MODEL` / `OPENAI_MODEL` | não (padrão `gpt-4o-mini`) | Modelo de chat |
| `EMBEDDING_MODEL` | não (padrão `BAAI/bge-m3`) | Embeddings do RAG |
| `RAG_K`, `RAG_FETCH_K` | não | Recuperação MMR no FAISS |

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
# 🤖 Assistente Médico com RAG e Validação Humana

Sistema de assistência clínica baseado em IA utilizando RAG (Retrieval-Augmented Generation), protocolos hospitalares e validação humana (HITL).

---

# 📌 Visão Geral

O assistente é executado via CLI interativa:

```bash
python main.py
```

O sistema:

- Recupera contexto relevante dos PDFs utilizando RAG
- Gera sugestões de conduta clínica
- Solicita validação humana antes da resposta final
- Utiliza fluxo multiagente com LangGraph

---

# 🧠 Tecnologias Utilizadas

- Python
- OpenAI
- Hugging Face
- LangChain
- LangGraph
- FAISS
- Pandas
- ReportLab
- RAG (Retrieval-Augmented Generation)
- HITL (Human-in-the-Loop)

---

# 🧭 Ordem Sugerida de Execução

## 1. Gerar PDFs e Dados Sintéticos

```bash
python gerar_dados.py
```

Esse processo irá:

- Gerar datasets médicos sintéticos
- Criar arquivos JSON
- Gerar PDFs hospitalares utilizados pelo RAG

---

## 2. Executar o Assistente

```bash
python main.py
```

Digite sua pergunta clínica e o sistema irá:

1. Recuperar contexto dos protocolos hospitalares
2. Gerar uma sugestão de conduta
3. Solicitar aprovação humana antes da finalização

---

## 3. Fine-Tuning (Opcional)

Notebook disponível em:

```text
notebooks/eda.ipynb
```

Responsável:

```text
integrante do grupo
```

---

# 🧩 Estrutura dos Módulos Python

| Arquivo | Responsabilidade |
|---|---|
| `gerar_dados.py` | Geração de JSONs e PDFs |
| `config.py` | Configurações e paths |
| `rag.py` | Embeddings, FAISS e retriever |
| `agentes.py` | Agentes pesquisador, analista e validador |
| `grafo.py` | Fluxo multiagente com LangGraph |
| `main.py` | CLI principal do assistente |

---

# 🔍 Funcionamento do Sistema

## Pipeline Geral

```text
Pergunta do usuário
        ↓
Busca vetorial (FAISS)
        ↓
Recuperação de contexto dos PDFs
        ↓
Análise com LLM
        ↓
Sugestão de conduta clínica
        ↓
Validação humana (HITL)
        ↓
Resposta final
```

---

# 🧠 Componentes Principais

## 🔹 RAG (Retrieval-Augmented Generation)

O sistema utiliza RAG para recuperar informações relevantes dos protocolos hospitalares antes de gerar respostas.

Fluxo:

- PDFs hospitalares → embeddings
- Embeddings → índice vetorial FAISS
- Busca semântica → contexto relevante
- Contexto → enviado ao modelo de IA

---

## 🔹 Embeddings

Os embeddings podem ser gerados utilizando modelos da Hugging Face ou OpenAI.

Exemplos:

- `sentence-transformers/all-MiniLM-L6-v2`
- `BAAI/bge-base-en`
- `text-embedding-3-small`

---

## 🔹 FAISS

Responsável pela indexação vetorial e busca semântica eficiente dos documentos médicos.

---

## 🔹 LangGraph

Coordena o fluxo dos agentes:

- Pesquisador
- Analista
- Validador

---

## 🔹 HITL (Human-in-the-Loop)

Antes da resposta final:

- o sistema solicita aprovação humana
- reduz riscos clínicos
- aumenta segurança operacional

---

# 🎯 Objetivos do Tech Challenge

- Fine-tuning com dados médicos
- Assistente baseado em protocolos internos
- Segurança com validação humana
- Uso de RAG para apoio clínico
- Arquitetura modular em Python
- Documentação técnica via README

---

# 📁 Estrutura Sugerida do Projeto

```text
projeto/
│
├── data/
│   ├── json/
│   ├── pdfs/
│   └── vetores/
│
├── notebooks/
│   └── eda.ipynb
│
├── gerar_dados.py
├── config.py
├── rag.py
├── agentes.py
├── grafo.py
├── main.py
│
└── README.md
```

---

# 🚀 Exemplo de Execução

```bash
python main.py
```

### Entrada:

```text
Paciente com febre, tosse e saturação 89%
```

### Fluxo:

- Busca protocolos respiratórios
- Recupera contexto relevante
- Sugere conduta clínica
- Solicita validação humana

---

# 🛡️ Segurança

O sistema não substitui profissionais da saúde.

As respostas:

- servem como apoio clínico
- dependem de validação humana
- utilizam protocolos institucionais

---

# 📚 Conceitos Utilizados

## RAG

Retrieval-Augmented Generation combina:

- busca semântica
- recuperação de contexto
- geração com LLM

---

## Fine-Tuning

Permite especializar o modelo com:

- datasets médicos
- protocolos clínicos
- linguagem hospitalar

---

## Busca Vetorial

Utiliza embeddings para encontrar documentos semanticamente semelhantes.

---

# ✅ Resultado Esperado

Um assistente clínico capaz de:

- consultar protocolos hospitalares
- responder perguntas médicas
- apoiar decisões clínicas
- operar com validação humana
- utilizar arquitetura moderna baseada em IA

---