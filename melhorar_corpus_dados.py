"""
Ajustes de qualidade no corpus JSON (sem chamar OpenAI).

Uso:
  python melhorar_corpus_dados.py
  python melhorar_corpus_dados.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
JSON_DIR = BASE / "dados" / "json"
PRONTUARIO_PATH = BASE / "dados" / "prontuario_exemplo.json"


def _titulo_categoria(valor: str) -> str:
    if not valor or not valor.strip():
        return valor
    partes = valor.strip().split()
    return " ".join(p[:1].upper() + p[1:] if p else p for p in partes)


def variar_queixa_triagem(texto: str, registro_id: int) -> str:
    texto = texto.strip()
    prefixos = ("Queixa:", "Relato:", "Motivo da procura:")
    prefixo = prefixos[(registro_id - 1) % len(prefixos)]

    substituicoes = [
        (r"^Paciente com\s+", f"{prefixo} "),
        (r"^Paciente relata\s+", f"{prefixo} "),
        (r"^Paciente apresenta\s+", f"{prefixo} "),
        (r"^Paciente referindo\s+", f"{prefixo} "),
        (r"^Paciente diabético com\s+", f"{prefixo} Diabético com "),
        (r"^Paciente com\s+", f"{prefixo} "),
    ]
    for padrao, repl in substituicoes:
        novo, n = re.subn(padrao, repl, texto, count=1, flags=re.IGNORECASE)
        if n:
            return novo
    if not texto.lower().startswith(prefixo.lower()[:4]):
        return f"{prefixo} {texto[0].lower() + texto[1:] if texto else texto}"
    return texto


def variar_quadro_evolucao(texto: str, registro_id: int) -> str:
    texto = texto.strip()
    prefixos = ("Evolução:", "Quadro:", "Relato clínico:")
    prefixo = prefixos[(registro_id - 1) % len(prefixos)]

    substituicoes = [
        (r"^Paciente apresenta\s+", f"{prefixo} "),
        (r"^Paciente com\s+", f"{prefixo} "),
        (r"^Paciente diabético com\s+", f"{prefixo} Diabético com "),
        (r"^Pós-operatório de\s+", f"{prefixo} Pós-operatório de "),
        (r"^Criança com\s+", f"{prefixo} Criança com "),
        (r"^Recém-nascido com\s+", f"{prefixo} Recém-nascido com "),
    ]
    for padrao, repl in substituicoes:
        novo, n = re.subn(padrao, repl, texto, count=1, flags=re.IGNORECASE)
        if n:
            return novo
    return f"{prefixo} {texto}" if texto else texto


def melhorar_evolucoes(dados: list) -> int:
    alteracoes = 0
    for item in dados:
        cat_antiga = item.get("categoria", "")
        cat_nova = _titulo_categoria(cat_antiga)
        if cat_nova != cat_antiga:
            item["categoria"] = cat_nova
            alteracoes += 1
        c = item["conteudo"]
        qc_antigo = c.get("quadro_clinico", "")
        qc_novo = variar_quadro_evolucao(qc_antigo, int(item.get("id", 0)))
        if qc_novo != qc_antigo:
            c["quadro_clinico"] = qc_novo
            alteracoes += 1
    return alteracoes


def melhorar_triagens(dados: list) -> int:
    alteracoes = 0
    for item in dados:
        c = item["conteudo"]
        q_antiga = c.get("queixa_principal", "")
        q_nova = variar_queixa_triagem(q_antiga, int(item.get("id", 0)))
        if q_nova != q_antiga:
            c["queixa_principal"] = q_nova
            alteracoes += 1
    return alteracoes


def melhorar_faqs(dados: list) -> int:
    """Adiciona FAQs com grafia sem acento para busca lexical/RAG."""
    existentes = {d["conteudo"]["pergunta"].lower().strip() for d in dados}
    novos = [
        {
            "id": 31,
            "tipo": "faq",
            "categoria": "Prontuário Médico",
            "conteudo": {
                "pergunta": "O que e prontuario medico e qual sua importancia?",
                "resposta": (
                    "O prontuário médico (prontuario medico) é o registro clínico "
                    "completo do atendimento, essencial para continuidade do cuidado, "
                    "segurança e auditoria hospitalar."
                ),
            },
        },
        {
            "id": 32,
            "tipo": "faq",
            "categoria": "Admissão Hospitalar",
            "conteudo": {
                "pergunta": "Quais documentos sao necessarios para admissao hospitalar?",
                "resposta": (
                    "Para admissao hospitalar são necessários documento de identificação, "
                    "cartão do plano de saúde quando houver, encaminhamento médico e "
                    "exames prévios disponíveis."
                ),
            },
        },
        {
            "id": 33,
            "tipo": "faq",
            "categoria": "Exames e Diagnósticos",
            "conteudo": {
                "pergunta": "Como obter resultados de exames no hospital?",
                "resposta": (
                    "Os resultados de exames podem ser retirados no setor responsável "
                    "ou acessados pelo portal do paciente, conforme política institucional."
                ),
            },
        },
    ]
    adicionados = 0
    max_id = max((d.get("id", 0) for d in dados), default=0)
    for item in novos:
        pergunta = item["conteudo"]["pergunta"].lower().strip()
        if pergunta in existentes:
            continue
        if item["id"] <= max_id:
            item["id"] = max_id + 1
            max_id += 1
        dados.append(item)
        existentes.add(pergunta)
        adicionados += 1
    return adicionados


def melhorar_prontuario() -> int:
    pacientes = [
        {
            "paciente_id": "P001",
            "nome": "Paciente Exemplo Silva",
            "idade": 58,
            "alergias": ["dipirona"],
            "medicamentos_em_uso": ["losartana 50mg", "metformina 850mg"],
            "exames_pendentes": ["hemograma completo", "raio-x de tórax"],
            "sinais_vitais": {"spo2": 89, "febre": True, "pressao": "130/85"},
            "ultima_consulta": "2026-05-20",
        },
        {
            "paciente_id": "P002",
            "nome": "Paciente Exemplo Costa",
            "idade": 34,
            "alergias": [],
            "medicamentos_em_uso": [],
            "exames_pendentes": [],
            "sinais_vitais": {"spo2": 98, "febre": False, "pressao": "118/76"},
            "ultima_consulta": "2026-05-18",
        },
        {
            "paciente_id": "P003",
            "nome": "Paciente Exemplo Souza",
            "idade": 8,
            "alergias": ["penicilina"],
            "medicamentos_em_uso": ["salbutamol spray"],
            "exames_pendentes": ["radiografia de tórax"],
            "sinais_vitais": {"spo2": 91, "febre": True, "pressao": "95/60"},
            "ultima_consulta": "2026-05-22",
            "observacoes": "Criança com histórico de asma; risco respiratório em exacerbação.",
        },
        {
            "paciente_id": "P004",
            "nome": "Paciente Exemplo Lima",
            "idade": 45,
            "alergias": ["dipirona", "penicilina", "contraste iodado"],
            "medicamentos_em_uso": ["omeprazol 20mg"],
            "exames_pendentes": ["tomografia abdominal"],
            "sinais_vitais": {"spo2": 97, "febre": False, "pressao": "125/82"},
            "ultima_consulta": "2026-05-21",
            "observacoes": "Múltiplas alergias medicamentosas — revisar prescrição antes de HITL.",
        },
        {
            "paciente_id": "P005",
            "nome": "Paciente Exemplo Mendes",
            "idade": 72,
            "alergias": [],
            "medicamentos_em_uso": ["enalapril 10mg", "AAS 100mg"],
            "exames_pendentes": ["eletrocardiograma", "BNP"],
            "sinais_vitais": {"spo2": 88, "febre": False, "pressao": "150/95"},
            "ultima_consulta": "2026-05-23",
            "observacoes": "Idoso com dispneia e SpO2 limítrofe; priorizar avaliação cardiopulmonar.",
        },
        {
            "paciente_id": "P006",
            "nome": "Paciente Exemplo Ribeiro",
            "idade": 29,
            "alergias": ["látex"],
            "medicamentos_em_uso": ["sulfato ferroso"],
            "exames_pendentes": ["ultrassom obstétrico"],
            "sinais_vitais": {"spo2": 99, "febre": False, "pressao": "110/70"},
            "ultima_consulta": "2026-05-24",
            "observacoes": "Gestante 32 semanas; triagem obstétrica se queixa de sangramento.",
        },
    ]
    PRONTUARIO_PATH.write_text(
        json.dumps(pacientes, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(pacientes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Melhora qualidade dos JSON locais")
    parser.add_argument("--dry-run", action="store_true", help="Só relata alterações")
    args = parser.parse_args()

    relatorio = []

    evolucoes = json.loads((JSON_DIR / "evolucoes.json").read_text(encoding="utf-8"))
    n_evo = melhorar_evolucoes(evolucoes)
    relatorio.append(f"evolucoes.json: {n_evo} campos ajustados")

    triagens = json.loads((JSON_DIR / "triagens.json").read_text(encoding="utf-8"))
    n_tri = melhorar_triagens(triagens)
    relatorio.append(f"triagens.json: {n_tri} queixas reescritas")

    faqs = json.loads((JSON_DIR / "faqs.json").read_text(encoding="utf-8"))
    n_faq = melhorar_faqs(faqs)
    relatorio.append(f"faqs.json: +{n_faq} entradas (busca sem acento)")

    n_pront = melhorar_prontuario()
    relatorio.append(f"prontuario_exemplo.json: {n_pront} pacientes")

    print("=== melhorar_corpus_dados ===")
    for linha in relatorio:
        print(f"  {linha}")

    if args.dry_run:
        print("\n(dry-run: arquivos não gravados)")
        return 0

    (JSON_DIR / "evolucoes.json").write_text(
        json.dumps(evolucoes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (JSON_DIR / "triagens.json").write_text(
        json.dumps(triagens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (JSON_DIR / "faqs.json").write_text(
        json.dumps(faqs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("\nArquivos JSON atualizados. Rode: python gerar_dados.py --apenas-pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
