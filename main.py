from grafo import app
from config import estado_inicial
from rag import build_retriever

build_retriever()

print("=" * 60)
print("ASSISTENTE MÉDICO RAG + HITL")
print("Comandos: 'sair' para encerrar")
print("Opcional: informe ID do paciente (ex: P001) ou Enter para pular")
print("=" * 60)

historico = []
thread_counter = 0

while True:
    pergunta = input("\nPergunta: ").strip()

    if pergunta.lower() in ("sair", "exit", "quit"):
        print("\nEncerrando...")
        break

    if not pergunta:
        continue

    patient_id = input("ID do paciente (opcional, ex: P001): ").strip()

    thread_counter += 1
    entrada = estado_inicial(pergunta, historico=historico, patient_id=patient_id)
    run_config = {"configurable": {"thread_id": f"consulta_{thread_counter:03d}"}}

    estado_acumulado: dict = dict(entrada)

    try:
        for output in app.stream(entrada, run_config):
            for key, value in output.items():
                print(f"\nNó executado: {key}")
                if isinstance(value, dict):
                    estado_acumulado.update(value)
    except Exception as exc:
        print(f"\nErro durante a consulta: {exc}")
        print("Verifique OPENAI_API_KEY no arquivo .env")
        continue

    resposta_final = estado_acumulado.get("resposta") or estado_acumulado.get(
        "sugestao_conduta"
    )

    if estado_acumulado.get("validado_por_humano") and estado_acumulado.get("resposta"):
        print("\n" + "=" * 60)
        print("RESPOSTA APROVADA")
        print("=" * 60)
        print(estado_acumulado["resposta"])
        historico.append({"pergunta": pergunta, "resposta": estado_acumulado["resposta"]})
    elif resposta_final and not estado_acumulado.get("validado_por_humano"):
        print("\nConsulta não aprovada — revise a sugestão e tente novamente.")
    elif resposta_final:
        print("\nResposta:")
        print(resposta_final)

    print("\n" + "=" * 60)
