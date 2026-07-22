"""
Regras de negócio do bot "Auditor de Acessos v1.0":
validação de itens da fila e simulação de acesso ao sistema ERP.
"""
import time

from logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Levantado quando um item da fila não passa nas regras de validação
    (ex.: CPF em branco). Deve ser tratado como Erro de Item, não como falha
    do processo inteiro."""
    pass


def validar_item(item_data: dict) -> str:
    cpf = (item_data.get("cpf") or "").strip()
    if not cpf:
        raise ValidationError("CPF em branco — item inválido para auditoria.")
    return cpf


def acessar_erp(usuario: str, senha: str) -> bool:
    """Simula o login no ERP auditado.
    IMPORTANTE: a senha é usada apenas em memória e NUNCA é logada ou impressa.
    """
    logger.info(f"Acessando sistema com o usuário: {usuario}")
    time.sleep(1)  # simula latência de autenticação
    return True


def auditar_usuario(item_data: dict, usuario_erp: str, senha_erp: str) -> dict:
    """Executa a auditoria de um único usuário. Levanta ValidationError se o
    item for inválido; caso contrário retorna um dicionário com o resultado."""
    cpf = validar_item(item_data)
    acessar_erp(usuario_erp, senha_erp)
    time.sleep(1)  # simula a checagem de acessos em si
    return {
        "cpf": cpf,
        "nome": item_data.get("nome", ""),
        "sistema": item_data.get("sistema", ""),
        "status": "AUDITADO_OK",
    }
