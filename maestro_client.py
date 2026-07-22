"""
Encapsula toda a comunicação com o BotCity Maestro: log de execução, alertas,
credenciais (Vault), DataPool e artefatos.

Quando MAESTRO_ENABLED=false (ou VAULT_ENABLED=false) o cliente opera em modo
OFFLINE, usando stubs locais equivalentes. Isso permite testar 100% da lógica
de negócio e da resiliência do bot sem depender de um servidor Maestro real —
o comportamento observável (logs, fila, resumo) é o mesmo.
"""
import json
from pathlib import Path

from config import (
    MAESTRO_ENABLED,
    VAULT_ENABLED,
    MAESTRO_SERVER,
    MAESTRO_LOGIN,
    MAESTRO_KEY,
    DATAPOOL_LABEL,
    LOGS_DIR,
)
from logger import get_logger

logger = get_logger(__name__)


class MaestroClient:
    def __init__(self):
        self.enabled = MAESTRO_ENABLED
        self.vault_enabled = VAULT_ENABLED
        self._sdk = None
        self.task_id = None

        if self.enabled:
            self._connect()
        else:
            logger.warning("MAESTRO_ENABLED=false — rodando em modo OFFLINE (stub local).")

    # ---------------- Conexão ----------------
    def _connect(self):
        try:
            from botcity.maestro import BotMaestroSDK

            self._sdk = BotMaestroSDK()
            self._sdk.login(server=MAESTRO_SERVER, login=MAESTRO_LOGIN, key=MAESTRO_KEY)
            self.task_id = getattr(self._sdk, "task_id", None)
            logger.info("Conectado ao BotCity Maestro com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao conectar ao Maestro: {e}")
            raise

    # ---------------- Log de execução ----------------
    def log(self, message: str):
        if self.enabled and self._sdk:
            try:
                self._sdk.new_log_entry(activity_label="AuditorAcessos", values={"mensagem": message})
            except Exception as e:
                logger.error(f"Falha ao registrar log no Maestro: {e}")
        logger.info(message)

    # ---------------- Alertas ----------------
    def alert(self, title: str, message: str, alert_type: str = "ERROR"):
        if self.enabled and self._sdk:
            try:
                from botcity.maestro import AlertType

                tipo = getattr(AlertType, alert_type, AlertType.ERROR)
                self._sdk.alert(task_id=self.task_id, title=title, message=message, alert_type=tipo)
            except Exception as e:
                logger.error(f"Falha ao emitir alerta no Maestro: {e}")
        logger.warning(f"ALERTA [{alert_type}]: {title} — {message}")

    # ---------------- Credenciais (Vault) ----------------
    def get_credential(self, label: str, key: str) -> str:
        """Recupera uma credencial do Vault em tempo de execução.
        A senha nunca é logada — apenas usada em memória."""
        if self.vault_enabled and self._sdk:
            try:
                return self._sdk.get_credential(label=label, key=key)
            except Exception as e:
                logger.error(f"Falha ao buscar credencial '{label}/{key}' no Vault: {e}")
                raise
        logger.warning(f"VAULT_ENABLED=false — usando credencial fictícia local para '{label}/{key}'.")
        stub = {"username": "usuario.teste", "password": "SENHA_FICTICIA_OFFLINE"}
        return stub.get(key, "")

    # ---------------- DataPool ----------------
    def get_datapool(self, label: str = None):
        label = label or DATAPOOL_LABEL
        if self.enabled and self._sdk:
            try:
                return self._sdk.get_datapool(label=label)
            except Exception:
                return self._sdk.create_datapool(
                    label=label, columns=["cpf", "nome", "sistema"], auto_retry=False
                )
        return _OfflineDataPool(label)

    # ---------------- Artefatos ----------------
    def post_artifact(self, filepath: str, artifact_name: str = None):
        artifact_name = artifact_name or Path(filepath).name
        if self.enabled and self._sdk:
            try:
                self._sdk.post_artifact(task_id=self.task_id, artifact_name=artifact_name, filepath=filepath)
                logger.info(f"Artefato '{artifact_name}' postado no Maestro.")
                return
            except Exception as e:
                logger.error(f"Falha ao postar artefato no Maestro: {e}")
        logger.info(f"[OFFLINE] Artefato '{artifact_name}' mantido localmente em: {filepath}")

    # ---------------- Finalização da task ----------------
    def finish_task(self, status: str = "SUCCESS", message: str = ""):
        if self.enabled and self._sdk:
            try:
                from botcity.maestro import AutomationTaskFinishStatus

                st = getattr(AutomationTaskFinishStatus, status, AutomationTaskFinishStatus.SUCCESS)
                self._sdk.finish_task(task_id=self.task_id, status=st, message=message)
            except Exception as e:
                logger.error(f"Falha ao finalizar task no Maestro: {e}")
        logger.info(f"Execução finalizada — status={status} — {message}")


# ======================================================================
# Stub de DataPool para modo OFFLINE — persiste os itens em um JSON local
# em logs/, permitindo que Dispatcher e Performer rodem como processos
# separados mesmo sem servidor Maestro real.
# ======================================================================
class _OfflineDataPoolItem:
    def __init__(self, data: dict, index: int, pool: "_OfflineDataPool"):
        self._data = data
        self._index = index
        self._pool = pool

    def get(self, key):
        return self._data.get(key)

    def report(self, status: str, message: str = ""):
        self._pool._report(self._index, status, message)


class _OfflineDataPool:
    def __init__(self, label: str):
        self.label = label
        self.path = LOGS_DIR / f"datapool_{label}.json"
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, items: list):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    def create_items(self, items: list):
        existing = self._load()
        for item in items:
            item = dict(item)
            item.setdefault("_status", "PENDING")
            item.setdefault("_message", "")
            existing.append(item)
        self._save(existing)
        logger.info(f"[OFFLINE] {len(items)} itens adicionados à fila '{self.label}'.")

    def next(self):
        items = self._load()
        for idx, item in enumerate(items):
            if item.get("_status") == "PENDING":
                return _OfflineDataPoolItem(item, idx, self)
        return None

    def _report(self, index: int, status: str, message: str):
        items = self._load()
        items[index]["_status"] = status
        items[index]["_message"] = message
        self._save(items)
