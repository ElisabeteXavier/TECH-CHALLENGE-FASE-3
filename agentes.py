
import os
from config import MedicalState
from rag import get_retriever
from langchain_openai import ChatOpenAI
# ============================================================
# AGENTE PESQUISADOR (RAG)
# ============================================================

def agente_pesquisador(state: MedicalState):

    pergunta = state["pergunta"]

    docs = get_retriever().invoke(pergunta)

    contexto = "\n\n".join([doc.page_content for doc in docs])

    fontes = "\n".join([
        f"- {doc.metadata.get('fonte', 'desconhecida')}"
        for doc in docs
    ])

    contexto_final = f"""
CONTEXTO CLÍNICO:

{contexto}

FONTES:
{fontes}
"""

    return {
        "contexto_recuperado": contexto_final
    }



# ============================================================
# AGENTE ANALISTA CLÍNICO
# ============================================================

def agente_analista(state: MedicalState):

    llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")  # Adicionar api_key explícito
    )

    prompt = f"""
Você é um assistente clínico hospitalar especializado.

REGRAS IMPORTANTES:
- Responda SOMENTE com base no contexto fornecido.
- Nunca invente protocolos.
- Nunca invente medicamentos.
- Nunca gere diagnósticos definitivos.
- Se não houver informação suficiente, diga isso claramente.
- Cite os protocolos e fontes quando possível.
- Sua resposta NÃO substitui avaliação médica humana.
- Seja técnico, claro e objetivo.

CONTEXTO:
{state['contexto_recuperado']}

PERGUNTA:
{state['pergunta']}
"""

    resposta = llm.invoke(prompt)

    return {
        "sugestao_conduta": resposta.content
    }

# ============================================================
# VALIDAÇÃO HUMANA (HITL)
# ============================================================

def validar_sugestao(state: MedicalState):

    print("\n")
    print("=" * 60)
    print("REVISÃO MÉDICA NECESSÁRIA")
    print("=" * 60)

    print("\nPERGUNTA:")
    print(state["pergunta"])

    print("\nSUGESTÃO GERADA:")
    print(state["sugestao_conduta"])

    print("\n")

    confirmacao = input("Aprovar resposta? (s/n): ")

    aprovado = confirmacao.lower() == "s"

    return {
        "validado_por_humano": aprovado
    }
