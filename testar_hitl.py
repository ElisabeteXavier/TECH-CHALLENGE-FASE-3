"""
Suíte de testes do fluxo HITL (Etapa 3.2 do guia de progresso).

Cenários:
  A — aprovação (s): resposta final com marca HITL e auditoria
  B — reprovação (n): sem resposta final; loop analista → validador
  C — sem aprovação explícita: roteamento não libera finalização

Uso:
  python testar_hitl.py
  python testar_hitl.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from agentes import (
    definir_provedor_entrada_hitl,
    finalizar_consulta,
    validar_sugestao,
)
from config import BASE_DIR, MedicalState, estado_inicial
from grafo import rota_pos_validacao

SAIDA_PADRAO = BASE_DIR / "dados" / "externos" / "docs" / "hitl_testes_resultados.json"


def estado_hitl_teste() -> MedicalState:
    return estado_inicial(
        pergunta="Paciente com febre e SpO2 89%. Conduta inicial?",
        patient_id="P001",
    ) | {
        "sugestao_conduta": "Sugestão sintética para teste HITL.",
        "fontes": "protocolos.pdf | protocolos | pagina 1 | chunk_id teste",
        "fontes_rag": [
            {
                "fonte_arquivo": "protocolos.pdf",
                "categoria": "protocolos",
                "pagina": 1,
                "chunk_id": "protocolos_0001",
            }
        ],
        "dados_paciente": "Paciente P001 — teste",
        "alertas": ["SpO2 baixa: 89%"],
    }


def provedor_fixo(resposta: str):
    def _provider(_state: MedicalState) -> str:
        return resposta

    return _provider


def provedor_sequencia(respostas: list[str]):
    it = iter(respostas)

    def _provider(_state: MedicalState) -> str:
        try:
            return next(it)
        except StopIteration as exc:
            raise AssertionError("provedor HITL sem mais respostas") from exc

    return _provider


class CasoTeste:
    def __init__(self, caso_id: str, descricao: str, fn):
        self.caso_id = caso_id
        self.descricao = descricao
        self.fn = fn

    def executar(self) -> dict[str, Any]:
        try:
            detalhes = self.fn()
            return {
                "id": self.caso_id,
                "descricao": self.descricao,
                "ok": True,
                "detalhes": detalhes,
            }
        except Exception as exc:
            return {
                "id": self.caso_id,
                "descricao": self.descricao,
                "ok": False,
                "erro": f"{type(exc).__name__}: {exc}",
            }


def _limpar_provider():
    definir_provedor_entrada_hitl(None)


def teste_rota_aprovado() -> dict:
    destino = rota_pos_validacao({"validado_por_humano": True})
    assert destino == "finalizar", f"esperado finalizar, obteve {destino}"
    return {"destino": destino}


def teste_rota_rejeitado() -> dict:
    destino = rota_pos_validacao({"validado_por_humano": False})
    assert destino == "analista", f"esperado analista, obteve {destino}"
    return {"destino": destino}


def teste_validar_aprovacao() -> dict:
    definir_provedor_entrada_hitl(provedor_fixo("s"))
    try:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch("logging_auditoria.LOG_DIR", log_dir):
                out = validar_sugestao(estado_hitl_teste())
        assert out.get("validado_por_humano") is True
        return {"validado_por_humano": out["validado_por_humano"]}
    finally:
        _limpar_provider()


def teste_validar_reprovacao() -> dict:
    definir_provedor_entrada_hitl(provedor_fixo("n"))
    try:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch("logging_auditoria.LOG_DIR", log_dir):
                out = validar_sugestao(estado_hitl_teste())
        assert out.get("validado_por_humano") is False
        return {"validado_por_humano": out["validado_por_humano"]}
    finally:
        _limpar_provider()


def teste_cenario_a_aprovacao_com_resposta_final() -> dict:
    """Cenário A: s → finalizar → resposta com marca HITL."""
    definir_provedor_entrada_hitl(provedor_fixo("s"))
    try:
        state = dict(estado_hitl_teste())
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch("logging_auditoria.LOG_DIR", log_dir):
                state.update(validar_sugestao(state))
                assert state["validado_por_humano"] is True
                assert rota_pos_validacao(state) == "finalizar"
                state.update(finalizar_consulta(state))

        resposta = state.get("resposta", "")
        assert resposta, "resposta final vazia após aprovação"
        assert "HITL" in resposta or "revisão humana" in resposta.lower()
        assert "FONTES CONSULTADAS" in resposta
        return {
            "validado_por_humano": True,
            "tem_resposta_final": bool(resposta),
            "marca_hitl": True,
        }
    finally:
        _limpar_provider()


def teste_cenario_b_reprovacao_sem_resposta_final() -> dict:
    """Cenário B: n → volta ao analista; sem resposta final publicada."""
    definir_provedor_entrada_hitl(provedor_fixo("n"))
    try:
        state = dict(estado_hitl_teste())
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch("logging_auditoria.LOG_DIR", log_dir):
                state.update(validar_sugestao(state))

        assert state["validado_por_humano"] is False
        assert rota_pos_validacao(state) == "analista"
        assert not state.get("resposta"), "não deve existir resposta final sem aprovação"
        return {
            "validado_por_humano": False,
            "destino": "analista",
            "resposta_final": state.get("resposta") or "",
        }
    finally:
        _limpar_provider()


def teste_cenario_b_loop_reanalise_depois_aprova() -> dict:
    """n na 1ª revisão, s na 2ª — simula loop validador → analista → validador."""
    definir_provedor_entrada_hitl(provedor_sequencia(["n", "s"]))
    try:
        state = dict(estado_hitl_teste())
        ciclos = []

        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch("logging_auditoria.LOG_DIR", log_dir):
                state.update(validar_sugestao(state))
                ciclos.append(
                    {
                        "entrada": "n",
                        "validado": state["validado_por_humano"],
                        "rota": rota_pos_validacao(state),
                    }
                )
                assert not state["validado_por_humano"]

                state["sugestao_conduta"] = "Sugestão revisada após reprovação."
                state.update(validar_sugestao(state))
                ciclos.append(
                    {
                        "entrada": "s",
                        "validado": state["validado_por_humano"],
                        "rota": rota_pos_validacao(state),
                    }
                )
                state.update(finalizar_consulta(state))

        assert state["validado_por_humano"] is True
        assert state.get("resposta")
        return {"ciclos": ciclos, "resposta_gerada": True}
    finally:
        _limpar_provider()


def teste_sem_s_nao_finaliza() -> dict:
    """Sem 's', finalizar_consulta não deve ser acionado pelo grafo (rota → analista)."""
    state = dict(estado_hitl_teste())
    state["validado_por_humano"] = False
    rota = rota_pos_validacao(state)
    assert rota != "finalizar"
    # Lógica equivalente à de main.py
    exibir_aprovada = state.get("validado_por_humano") and state.get("resposta")
    assert not exibir_aprovada
    return {"rota": rota, "exibir_aprovada_main": exibir_aprovada}


def teste_auditoria_evento_hitl() -> dict:
    definir_provedor_entrada_hitl(provedor_fixo("s"))
    try:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with patch("logging_auditoria.LOG_DIR", log_dir):
                validar_sugestao(estado_hitl_teste())
            path = log_dir / "auditoria.jsonl"
            assert path.is_file(), "auditoria.jsonl não criado"
            linhas = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l]
        eventos = [r.get("evento") for r in linhas]
        assert "validacao_hitl" in eventos
        hitl = next(r for r in linhas if r["evento"] == "validacao_hitl")
        assert hitl.get("aprovado") is True
        assert hitl.get("fontes_rag")
        return {"eventos": eventos, "aprovado_log": hitl["aprovado"]}
    finally:
        _limpar_provider()


def montar_casos() -> list[CasoTeste]:
    return [
        CasoTeste("hitl_01", "Rota condicional → finalizar quando aprovado", teste_rota_aprovado),
        CasoTeste("hitl_02", "Rota condicional → analista quando reprovado", teste_rota_rejeitado),
        CasoTeste("hitl_03", "validar_sugestao com 's' marca aprovado", teste_validar_aprovacao),
        CasoTeste("hitl_04", "validar_sugestao com 'n' marca reprovado", teste_validar_reprovacao),
        CasoTeste(
            "hitl_05",
            "Cenário A: aprovação gera resposta final com HITL",
            teste_cenario_a_aprovacao_com_resposta_final,
        ),
        CasoTeste(
            "hitl_06",
            "Cenário B: reprovação não gera resposta final",
            teste_cenario_b_reprovacao_sem_resposta_final,
        ),
        CasoTeste(
            "hitl_07",
            "Cenário B+: loop n→s após reanálise",
            teste_cenario_b_loop_reanalise_depois_aprova,
        ),
        CasoTeste(
            "hitl_08",
            "Sem aprovação explícita: rota não libera finalização",
            teste_sem_s_nao_finaliza,
        ),
        CasoTeste(
            "hitl_09",
            "Auditoria JSONL registra validacao_hitl",
            teste_auditoria_evento_hitl,
        ),
    ]


def imprimir_relatorio(resultados: list[dict], verbose: bool) -> None:
    total = len(resultados)
    ok = sum(1 for r in resultados if r["ok"])
    print("\n=== Testes HITL ===")
    print(f"Passou: {ok}/{total}")
    for r in resultados:
        status = "OK" if r["ok"] else "FALHOU"
        print(f"  [{r['id']}] {status} — {r['descricao']}")
        if not r["ok"]:
            print(f"       erro: {r.get('erro', '')}")
        elif verbose and r.get("detalhes"):
            print(f"       {r['detalhes']}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa suíte de testes HITL")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()

    resultados = [c.executar() for c in montar_casos()]
    imprimir_relatorio(resultados, args.verbose)

    relatorio = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(resultados),
        "passou": sum(1 for r in resultados if r["ok"]),
        "falhou": sum(1 for r in resultados if not r["ok"]),
        "casos": resultados,
    }
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with open(args.saida, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, ensure_ascii=False, indent=2)
    print(f"Resultados salvos em: {args.saida}")

    return 0 if relatorio["falhou"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
