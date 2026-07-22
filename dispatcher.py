"""
Etapa A — Dispatcher.
Lê o CSV de entrada (dados_entrada/usuarios_auditoria.csv) e envia cada linha
como um item para o DataPool configurado (FilaAuditoriaRH).
"""
import csv
import sys

from config import DADOS_ENTRADA_DIR, CSV_ENTRADA, DATAPOOL_LABEL, ensure_dirs
from logger import get_logger
from maestro_client import MaestroClient

logger = get_logger(__name__)


def validar_pasta_entrada() -> bool:
    return DADOS_ENTRADA_DIR.exists() and DADOS_ENTRADA_DIR.is_dir()


def ler_csv() -> list:
    caminho = DADOS_ENTRADA_DIR / CSV_ENTRADA
    if not caminho.exists():
        raise FileNotFoundError(caminho)

    itens = []
    with open(caminho, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            itens.append(
                {
                    "cpf": (row.get("cpf") or "").strip(),
                    "nome": (row.get("nome") or "").strip(),
                    "sistema": (row.get("sistema") or "").strip(),
                }
            )
    return itens


def main():
    ensure_dirs()
    maestro = MaestroClient()
    maestro.log("Dispatcher: iniciando carga da fila de auditoria")

    # Fail Fast: sem a pasta de entrada, não há o que processar
    if not validar_pasta_entrada():
        msg = f"A pasta '{DADOS_ENTRADA_DIR}' não existe. Dispatcher encerrado (Fail Fast)."
        logger.error(msg)
        maestro.alert(title="Pasta de dados de entrada ausente", message=msg)
        sys.exit(1)

    try:
        itens = ler_csv()
    except FileNotFoundError:
        msg = f"Arquivo '{CSV_ENTRADA}' não encontrado em {DADOS_ENTRADA_DIR}."
        logger.error(msg)
        maestro.alert(title="Arquivo CSV ausente", message=msg)
        sys.exit(1)

    if not itens:
        logger.warning("CSV lido, mas nenhum item foi encontrado.")

    datapool = maestro.get_datapool(DATAPOOL_LABEL)
    datapool.create_items(itens)

    maestro.log(f"Dispatcher: {len(itens)} itens enviados para a fila '{DATAPOOL_LABEL}'")


if __name__ == "__main__":
    main()
