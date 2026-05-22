from grafo import app
from rag import build_retriever

# Inicializa o retriever uma única vez
build_retriever()

print("=" * 60)
print("ASSISTENTE MÉDICO RAG")
print("Digite 'sair' para encerrar")
print("=" * 60)

historico = []

while True:
    pergunta = input("\nPergunta: ")

    if pergunta.lower() in ["sair", "exit", "quit"]:
        print("\nEncerrando...")
        break

    entrada = {
        "pergunta": pergunta,
        "historico": historico,
    }

    run_config = {
        "configurable": {"thread_id": "consulta_001"},
    }

    resposta_final = None

    for output in app.stream(entrada, run_config):

        for key, value in output.items():
            print(f"\nNó executado: {key}")

            # captura resposta final se existir
            if isinstance(value, dict) and "resposta" in value:
                resposta_final = value["resposta"]

    if resposta_final:
        print("\nResposta:")
        print(resposta_final)

        historico.append({
            "pergunta": pergunta,
            "resposta": resposta_final
        })

    print("\n" + "=" * 60)