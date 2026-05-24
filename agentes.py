import os

from langchain_openai import ChatOpenAI

from config import LLM_MODEL, MedicalState
from logging_auditoria import registrar_auditoria
from rag import formatar_fonte_metadata, get_retriever

# ============================================================
# AGENTE PRONTUÁRIO — integrado em prontuario.py
# ============================================================

# ============================================================
# AGENTE PESQUISADOR (RAG)
# ============================================================


def agente_pesquisador(state: MedicalState):
    pergunta = state["pergunta"]
    docs = get_retriever().invoke(pergunta)

    contexto = "\n\n".join([doc.page_content for doc in docs])
    fontes = "\n".join(f"- {formatar_fonte_metadata(doc.metadata)}" for doc in docs)

    bloco_paciente = ""
    if state.get("dados_paciente"):
        bloco_paciente = f"\nPRONTUÁRIO DO PACIENTE:\n{state['dados_paciente']}\n"

    alertas = state.get("alertas") or []
    bloco_alertas = ""
    if alertas:
        bloco_alertas = "\nALERTAS:\n" + "\n".join(f"- {a}" for a in alertas) + "\n"

    contexto_final = f"""
CONTEXTO CLÍNICO (protocolos hospitalares):
{contexto}
{bloco_paciente}{bloco_alertas}
FONTES RECUPERADAS:
{fontes}
"""

    return {
        "contexto_recuperado": contexto_final,
        "fontes": fontes,
    }


# ============================================================
# AGENTE ANALISTA CLÍNICO
# ============================================================


def agente_analista(state: MedicalState):
    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = f"""
Você é um assistente clínico hospitalar de APOIO à decisão (não substitui o médico).

REGRAS OBRIGATÓRIAS:
- Responda SOMENTE com base no contexto fornecido.
- Nunca invente protocolos, medicamentos ou doses.
- Nunca gere diagnóstico definitivo nem prescrição direta.
- Se a informação for insuficiente, declare explicitamente.
- Cite as fontes listadas em FONTES RECUPERADAS.
- Use raciocínio passo a passo (Chain of Thought) antes da conduta sugerida.

FORMATO DA RESPOSTA (português):
1. Análise breve do caso
2. Passos de raciocínio
3. Sugestão de conduta (não vinculante)
4. Fontes utilizadas
5. Aviso: requer validação de profissional habilitado

CONTEXTO:
{state.get('contexto_recuperado', '')}

PERGUNTA:
{state['pergunta']}
"""

    resposta = llm.invoke(prompt)
    return {"sugestao_conduta": resposta.content}


# ============================================================
# VALIDAÇÃO HUMANA (HITL)
# ============================================================


def validar_sugestao(state: MedicalState):
    print("\n")
    print("=" * 60)
    print("REVISÃO MÉDICA NECESSÁRIA")
    print("=" * 60)

    if state.get("dados_paciente"):
        print("\nPRONTUÁRIO:")
        print(state["dados_paciente"])

    alertas = state.get("alertas") or []
    if alertas:
        print("\nALERTAS:")
        for alerta in alertas:
            print(f"  - {alerta}")

    print("\nPERGUNTA:")
    print(state["pergunta"])

    print("\nSUGESTÃO GERADA:")
    print(state.get("sugestao_conduta", ""))

    if state.get("fontes"):
        print("\nFONTES (RAG):")
        print(state["fontes"])

    print("\n")
    confirmacao = input("Aprovar resposta? (s/n): ")
    aprovado = confirmacao.strip().lower() == "s"

    registrar_auditoria(
        {
            "evento": "validacao_hitl",
            "pergunta": state["pergunta"],
            "patient_id": state.get("patient_id", ""),
            "aprovado": aprovado,
            "fontes": state.get("fontes", ""),
        }
    )

    return {"validado_por_humano": aprovado}


# ============================================================
# FINALIZAÇÃO E LOG
# ============================================================


def finalizar_consulta(state: MedicalState):
    """Monta resposta final após aprovação humana."""
    resposta = (
        f"{state.get('sugestao_conduta', '')}\n\n"
        f"---\n"
        f"FONTES CONSULTADAS (RAG):\n{state.get('fontes', 'Nenhuma')}\n\n"
        f"✓ Resposta aprovada em revisão humana (HITL).\n"
        f"⚠️ Não substitui avaliação médica presencial."
    )
    return {"resposta": resposta}


def registrar_log(state: MedicalState):
    registrar_auditoria(
        {
            "evento": "consulta_finalizada",
            "pergunta": state["pergunta"],
            "patient_id": state.get("patient_id", ""),
            "aprovado": state.get("validado_por_humano", False),
            "resposta_preview": (state.get("resposta") or "")[:500],
            "fontes": state.get("fontes", ""),
        }
    )
    return {}
