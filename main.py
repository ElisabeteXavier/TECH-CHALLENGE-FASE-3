"""
CLI principal do Assistente Médico — RAG + HITL.

Fluxos disponíveis:
  1. Triagem Ginecológica
  2. Detecção de Violência Doméstica
  3. Fluxo Obstétrico
  4. Prevenção e Acompanhamento
  0. Fluxo genérico (grafo.py original)
"""

from grafo import app as app_generico
from config import estado_inicial
from rag import build_retriever

build_retriever()

MENU = """
╔══════════════════════════════════════════════════╗
║     ASSISTENTE MÉDICO — RAG + HITL               ║
╠══════════════════════════════════════════════════╣
║  1. Triagem Ginecológica                         ║
║  2. Detecção de Violência Doméstica              ║
║  3. Fluxo Obstétrico                             ║
║  4. Prevenção e Acompanhamento                   ║
║  0. Fluxo Genérico                               ║
║  s. Sair                                         ║
╚══════════════════════════════════════════════════╝
"""

FLUXO_NOMES = {
    "0": "Fluxo Genérico",
    "1": "Triagem Ginecológica",
    "2": "Detecção de Violência Doméstica",
    "3": "Fluxo Obstétrico",
    "4": "Prevenção e Acompanhamento",
}


def _selecionar_app():
    """Exibe menu e retorna (app_compilado, nome_fluxo)."""
    print(MENU)
    while True:
        escolha = input("Escolha o fluxo: ").strip().lower()
        if escolha in ("s", "sair", "exit", "quit"):
            return None, "sair"
        if escolha == "0":
            return app_generico, FLUXO_NOMES["0"]
        if escolha in ("1", "2", "3", "4"):
            try:
                from grafo_saude_mulher import build_grafo, NOMES_FLUXOS
                mapa = {"1": "triagem", "2": "violencia", "3": "obstetrico", "4": "prevencao"}
                nome_chave = mapa[escolha]
                print(f"\n→ Fluxo selecionado: {NOMES_FLUXOS[nome_chave]}\n")
                return build_grafo(nome_chave), NOMES_FLUXOS[nome_chave]
            except ImportError:
                print("\n⚠️  grafo_saude_mulher.py não encontrado. Usando fluxo genérico.\n")
                return app_generico, f"{FLUXO_NOMES[escolha]} (fluxo genérico)"
        print("Opção inválida. Digite 1, 2, 3, 4, 0 ou s.")


def _executar_consulta(app, pergunta, patient_id, historico, thread_id):
    entrada = estado_inicial(pergunta, historico=historico, patient_id=patient_id)
    run_config = {"configurable": {"thread_id": thread_id}}
    estado_acumulado = dict(entrada)

    for output in app.stream(entrada, run_config):
        for key, value in output.items():
            print(f"\n  [nó: {key}]")
            if isinstance(value, dict):
                estado_acumulado.update(value)

    return estado_acumulado


def main():
    print("=" * 60)
    print("ASSISTENTE MÉDICO RAG + HITL")
    print("Comandos: 'menu' para trocar de fluxo | 'sair' para encerrar")
    print("=" * 60)

    historico = []
    thread_counter = 0
    app_ativo, nome_fluxo = _selecionar_app()

    if app_ativo is None:
        print("\nEncerrando...")
        return

    while True:
        pergunta = input("\nPergunta: ").strip()

        if pergunta.lower() in ("sair", "exit", "quit"):
            print("\nEncerrando...")
            break

        if pergunta.lower() == "menu":
            app_ativo, nome_fluxo = _selecionar_app()
            if app_ativo is None:
                print("\nEncerrando...")
                break
            historico = []
            continue

        if not pergunta:
            continue

        patient_id = input("ID do paciente (opcional, ex: P001): ").strip()

        thread_counter += 1
        thread_id = f"consulta_{thread_counter:03d}"

        print(f"\n[Executando: {nome_fluxo}]")

        try:
            estado = _executar_consulta(
                app_ativo, pergunta, patient_id, historico, thread_id
            )
        except Exception as exc:
            print(f"\nErro durante a consulta: {exc}")
            print("Verifique OPENAI_API_KEY no arquivo .env")
            continue

        resposta_final = estado.get("resposta") or estado.get("sugestao_conduta")

        print("\n" + "=" * 60)
        if estado.get("validado_por_humano") and estado.get("resposta"):
            print("RESPOSTA APROVADA")
            print("=" * 60)
            print(estado["resposta"])
            historico.append({"pergunta": pergunta, "resposta": estado["resposta"]})
        elif resposta_final and not estado.get("validado_por_humano"):
            print("Consulta não aprovada — revise a sugestão e tente novamente.")
        elif resposta_final:
            print("Resposta:")
            print(resposta_final)
        print("=" * 60)


if __name__ == "__main__":
    main()
