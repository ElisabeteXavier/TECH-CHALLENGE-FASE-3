from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from config import MedicalState
from agentes import agente_pesquisador, agente_analista, validar_sugestao

# ============================================================
# DEFINIÇÃO DO GRAFO
# ============================================================

workflow = StateGraph(MedicalState)


# ============================================================
# NÓS
# ============================================================

workflow.add_node(
    "pesquisador",
    agente_pesquisador
)

workflow.add_node(
    "analista",
    agente_analista
)

workflow.add_node(
    "validador",
    validar_sugestao
)

# ============================================================
# FLUXO
# ============================================================

workflow.set_entry_point("pesquisador")

workflow.add_edge(
    "pesquisador",
    "analista"
)

workflow.add_edge(
    "analista",
    "validador"
)


# ============================================================
# ROTA CONDICIONAL
# ============================================================

def rota_pos_validacao(state: MedicalState):

    if state["validado_por_humano"]:
        return "fim"

    return "analista"


workflow.add_conditional_edges(
    "validador",
    rota_pos_validacao,
    {
        "fim": END,
        "analista": "analista"
    }
)


# ============================================================
# CHECKPOINT / MEMÓRIA
# ============================================================

memoria = MemorySaver()

app = workflow.compile(
    checkpointer=memoria
)
