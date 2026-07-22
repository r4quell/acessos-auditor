"""
Logger padronizado do projeto: escreve em logs/execucao.log e no console,
sempre com timestamp, nível de severidade e mensagem.
"""
import logging

from config import LOG_FILE, ensure_dirs

_LOGGERS = {}


def get_logger(name: str = "auditor_acessos") -> logging.Logger:
    if name in _LOGGERS:
        return _LOGGERS[name]

    ensure_dirs()

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _LOGGERS[name] = logger
    return logger
