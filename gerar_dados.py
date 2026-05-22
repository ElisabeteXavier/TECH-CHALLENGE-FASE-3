"""
Gera JSON + PDF dos dados hospitalares sintéticos.

- Se o JSON já existir em dados/json/, usa ele (não chama OpenAI).
- Se não existir, gera via OpenAI e salva.

Uso:
  python gerar_dados.py
  python gerar_dados.py --force          # regera tudo pela API
  python gerar_dados.py --apenas-pdf     # só PDFs a partir dos JSON existentes
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph,Preformatted, SimpleDocTemplate, Spacer

BASE = Path(__file__).resolve().parent
PASTA_JSON = BASE / "dados" / "json"
PASTA_PDF = BASE / "dados" / "pdfs"

CATEGORIAS = ["faqs", "protocolos", "laudos", "receitas", "triagens", "evolucoes"]

PROMPTS = {
    "faqs": """
Você é um especialista em documentação hospitalar.

Gere 30 FAQs médicas hospitalares.

Formato JSON:
[
  {
    "id": 1,
    "tipo": "faq",
    "categoria": "",
    "conteudo": {
      "pergunta": "",
      "resposta": ""
    }
  }
]
""",
    "protocolos": """
Você é um especialista em protocolos hospitalares.

Gere 20 protocolos clínicos sintéticos hospitalares.

Formato JSON:
[
  {
    "id": 1,
    "tipo": "protocolo",
    "categoria": "",
    "conteudo": {
      "titulo": "",
      "descricao": "",
      "conduta": ""
    }
  }
]
""",
    "laudos": """
Você é um especialista em laudos médicos.

Gere 20 laudos médicos sintéticos.

Formato JSON:
[
  {
    "id": 1,
    "tipo": "laudo",
    "categoria": "",
    "conteudo": {
      "exame": "",
      "resultado": "",
      "conclusao": ""
    }
  }
]
""",
    "receitas": """
Você é um especialista em prescrições médicas.

Gere 20 receitas médicas sintéticas.

Formato JSON:
[
  {
    "id": 1,
    "tipo": "receita",
    "categoria": "",
    "conteudo": {
      "medicamento": "",
      "dosagem": "",
      "orientacao": ""
    }
  }
]
""",
    "triagens": """
Você é um especialista em triagem hospitalar.

Gere 20 triagens sintéticas.

Formato JSON:
[
  {
    "id": 1,
    "tipo": "triagem",
    "categoria": "",
    "conteudo": {
      "queixa_principal": "",
      "sinais_vitais": "",
      "classificacao_risco": ""
    }
  }
]
""",
    "evolucoes": """
Você é um especialista em evolução médica hospitalar.

Gere 20 evoluções médicas sintéticas.

Formato JSON:
[
  {
    "id": 1,
    "tipo": "evolucao",
    "categoria": "",
    "conteudo": {
      "quadro_clinico": "",
      "conduta": "",
      "observacao": ""
    }
  }
]
""",
}

styles = getSampleStyleSheet()


def gerar_pdf(nome: str, dados: list) -> Path:
    PASTA_PDF.mkdir(parents=True, exist_ok=True)
    pdf_path = PASTA_PDF / f"{nome}.pdf"

    pdf = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    elementos = [
        Paragraph(f"<b>{nome.upper()}</b>", styles["Title"]),
        Spacer(1, 20),
    ]

    for item in dados:
        texto = f"""
        <b>ID:</b> {item.get("id")}<br/><br/>
        <b>Tipo:</b> {item.get("tipo")}<br/><br/>
        <b>Categoria:</b> {item.get("categoria")}<br/><br/>
        <b>Conteúdo:</b><br/><br/>
        {json.dumps(item.get("conteudo"), ensure_ascii=False, indent=2)}
        """
        elementos.append(Preformatted(texto,styles["Code"]))
        elementos.append(Spacer(1, 12))
        elementos.append(HRFlowable(width="100%"))
        elementos.append(Spacer(1, 12))

    pdf.build(elementos)
    print(f"  PDF salvo: {pdf_path}")
    return pdf_path


def carregar_json(categoria: str) -> list:
    path = PASTA_JSON / f"{categoria}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def salvar_json(categoria: str, dados: list) -> Path:
    PASTA_JSON.mkdir(parents=True, exist_ok=True)
    path = PASTA_JSON / f"{categoria}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  JSON salvo: {path}")
    return path


def gerar_json_openai(categoria: str, client) -> list:
    prompt = PROMPTS[categoria]
    print(f"  Chamando OpenAI para gerar JSON...")

    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )

    conteudo = response.choices[0].message.content or ""
    conteudo = conteudo.replace("```json", "").replace("```", "").strip()
    return json.loads(conteudo)


def processar_categoria(categoria: str, client, force: bool, apenas_pdf: bool) -> None:
    print(f"\n[{categoria}]")
    json_path = PASTA_JSON / f"{categoria}.json"
    json_existe = json_path.is_file() and json_path.stat().st_size > 0

    if apenas_pdf:
        if not json_existe:
            print(f"  Pulando: JSON não encontrado em {json_path}")
            return
        dados = carregar_json(categoria)
        print(f"  JSON já existia — gerando só PDF")
        gerar_pdf(categoria, dados)
        return

    if json_existe and not force:
        dados = carregar_json(categoria)
        print(f"  JSON já existia — usando arquivo local (sem OpenAI)")
    else:
        if force and json_existe:
            print(f"  --force: regerando JSON via OpenAI")
        if client is None:
            print("  ERRO: JSON não existe e OPENAI_API_KEY não configurada.")
            sys.exit(1)
        dados = gerar_json_openai(categoria, client)
        salvar_json(categoria, dados)

    gerar_pdf(categoria, dados)


def main():
    parser = argparse.ArgumentParser(description="Gera dados hospitalares (JSON + PDF)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regera JSON pela OpenAI mesmo se o arquivo já existir",
    )
    parser.add_argument(
        "--apenas-pdf",
        action="store_true",
        help="Só gera PDFs a partir dos JSON em dados/json/",
    )
    args = parser.parse_args()

    load_dotenv()
    PASTA_JSON.mkdir(parents=True, exist_ok=True)
    PASTA_PDF.mkdir(parents=True, exist_ok=True)

    client = None
    if not args.apenas_pdf:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        elif args.force:
            print("ERRO: --force exige OPENAI_API_KEY no .env")
            sys.exit(1)

    for categoria in CATEGORIAS:
        processar_categoria(categoria, client, args.force, args.apenas_pdf)

    print("\nFINALIZADO.")


if __name__ == "__main__":
    main()