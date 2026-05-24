from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from agentes import (
    agente_analista,
    agente_pesquisador,
    finalizar_consulta,
    registrar_log,
    validar_sugestao,
)
from config import MedicalState
from prontuario import carregar_prontuario

workflow = StateGraph(MedicalState)

workflow.add_node("prontuario", carregar_prontuario)
workflow.add_node("pesquisador", agente_pesquisador)
workflow.add_node("analista", agente_analista)
workflow.add_node("validador", validar_sugestao)
workflow.add_node("finalizar", finalizar_consulta)
workflow.add_node("log", registrar_log)

workflow.set_entry_point("prontuario")
workflow.add_edge("prontuario", "pesquisador")
workflow.add_edge("pesquisador", "analista")
workflow.add_edge("analista", "validador")


def rota_pos_validacao(state: MedicalState):
    if state.get("validado_por_humano"):
        return "finalizar"
    return "analista"


workflow.add_conditional_edges(
    "validador",
    rota_pos_validacao,
    {"finalizar": "finalizar", "analista": "analista"},
)
workflow.add_edge("finalizar", "log")
workflow.add_edge("log", END)

memoria = MemorySaver()
app = workflow.compile(checkpointer=memoria)
