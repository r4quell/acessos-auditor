"""
Configuração central do bot.
Todas as variáveis vêm do .env — nenhum caminho ou segredo é hardcoded aqui.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# --- Diretórios / arquivos de dados ---
DADOS_ENTRADA_DIR = BASE_DIR / os.getenv("DADOS_ENTRADA_DIR", "dados_entrada")
LOGS_DIR = BASE_DIR / os.getenv("LOGS_DIR", "logs")
LOG_FILE = LOGS_DIR / "execucao.log"
CSV_ENTRADA = os.getenv("CSV_ENTRADA", "usuarios_auditoria.csv")

# --- BotCity Maestro ---
MAESTRO_ENABLED = os.getenv("MAESTRO_ENABLED", "false").strip().lower() == "true"
VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").strip().lower() == "true"
MAESTRO_SERVER = os.getenv("MAESTRO_SERVER", "")
MAESTRO_LOGIN = os.getenv("MAESTRO_LOGIN", "")
MAESTRO_KEY = os.getenv("MAESTRO_KEY", "")

DATAPOOL_LABEL = os.getenv("DATAPOOL_LABEL", "FilaAuditoriaRH")
CREDENTIAL_LABEL = os.getenv("CREDENTIAL_LABEL", "credencial_erp")


def ensure_dirs():
    """Garante que a pasta de logs existe (a pasta de dados de entrada é validada
    separadamente, pois sua ausência deve provocar Fail Fast, não criação automática)."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
