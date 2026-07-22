"""
Etapa B — Performer / Bot Principal "Auditor de Acessos v1.0".

Consome os itens da fila FilaAuditoriaRH, executa a auditoria de cada usuário,
trata erros de item sem interromper o lote e, ao final, gera e posta um
relatório (ExecutionResult) como artefato no Maestro.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from config import DADOS_ENTRADA_DIR, DATAPOOL_LABEL, CREDENTIAL_LABEL, LOGS_DIR, ensure_dirs
from logger import get_logger
from maestro_client import MaestroClient
from bot import auditar_usuario, ValidationError

logger = get_logger(__name__)


class ExecutionResult:
    """Padroniza o resumo de uma execução, usado tanto para logs quanto para
    o artefato JSON postado no Maestro ao final do processamento."""

    def __init__(self):
        self.inicio = datetime.now()
        self.fim = None
        self.total_processados = 0
        self.total_sucesso = 0
        self.total_erro = 0
        self.erros = []

    def registrar_sucesso(self):
        self.total_processados += 1
        self.total_sucesso += 1

    def registrar_erro(self, item_data: dict, motivo: str):
        self.total_processados += 1
        self.total_erro += 1
        self.erros.append({"item": item_data, "motivo": motivo})

    def finalizar(self):
        self.fim = datetime.now()

    def to_dict(self) -> dict:
        return {
            "inicio": self.inicio.isoformat(),
            "fim": self.fim.isoformat() if self.fim else None,
            "duracao_segundos": (self.fim - self.inicio).total_seconds() if self.fim else None,
            "total_processados": self.total_processados,
            "total_sucesso": self.total_sucesso,
            "total_erro": self.total_erro,
            "erros": self.erros,
        }

    def salvar_json(self, caminho: Path):
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


def main():
    ensure_dirs()

    # ---- Fail Fast: a pasta de dados de entrada precisa existir ----
    if not DADOS_ENTRADA_DIR.exists():
        maestro = MaestroClient()
        msg = f"Pasta de dados de entrada não encontrada: {DADOS_ENTRADA_DIR}. Execução abortada (Fail Fast)."
        logger.error(msg)
        maestro.alert(title="Falha de pré-requisito", message=msg)
        maestro.finish_task(status="FAILED", message=msg)
        sys.exit(1)

    maestro = MaestroClient()
    maestro.log("Iniciando auditoria de acessos")

    # ---- Credenciais via Vault (senha nunca é logada) ----
    usuario_erp = maestro.get_credential(CREDENTIAL_LABEL, "username")
    senha_erp = maestro.get_credential(CREDENTIAL_LABEL, "password")

    datapool = maestro.get_datapool(DATAPOOL_LABEL)
    resultado = ExecutionResult()

    while True:
        item = datapool.next()
        if item is None:
            break

        item_data = {
            "cpf": item.get("cpf"),
            "nome": item.get("nome"),
            "sistema": item.get("sistema"),
        }

        try:
            auditar_usuario(item_data, usuario_erp, senha_erp)
            item.report(status="DONE", message="Auditado com sucesso")
            resultado.registrar_sucesso()
            logger.info(f"Item processado com sucesso: {item_data.get('nome')} ({item_data.get('cpf')})")
        except ValidationError as e:
            item.report(status="ERROR", message=str(e))
            resultado.registrar_erro(item_data, str(e))
            logger.error(f"Erro de item {item_data}: {e}")
        except Exception as e:
            item.report(status="ERROR", message=f"Erro inesperado: {e}")
            resultado.registrar_erro(item_data, f"Erro inesperado: {e}")
            logger.error(f"Erro inesperado ao processar item {item_data}: {e}")

    resultado.finalizar()

    relatorio_path = LOGS_DIR / "relatorio_execucao.json"
    resultado.salvar_json(relatorio_path)
    maestro.post_artifact(filepath=str(relatorio_path), artifact_name="relatorio_execucao.json")

    status_final = "SUCCESS" if resultado.total_erro == 0 else "PARTIAL_SUCCESS"
    maestro.finish_task(
        status=status_final,
        message=f"{resultado.total_sucesso} sucesso(s), {resultado.total_erro} erro(s)",
    )

    logger.info(f"Execução concluída: {resultado.to_dict()}")


if __name__ == "__main__":
    main()
