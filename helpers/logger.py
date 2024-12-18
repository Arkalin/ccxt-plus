import logging
from logging.handlers import RotatingFileHandler
import os

from helpers.config import Config


class Logger:
    _logger = None

    @staticmethod
    def _initialize():
        if not Logger._logger:
            Logger._logger = logging.getLogger("logger")
            Logger._logger.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            if not Logger._logger.handlers:

                if Config("CONSOLE_LOG"):
                    console_handler = logging.StreamHandler()
                    console_handler.setLevel(logging.INFO)
                    Logger._logger.addHandler(console_handler)
                    console_handler.setFormatter(formatter)
                if Config("FILE_LOG"):
                    os.makedirs(Config("LOG_PATH"), exist_ok=True)
                    _log_file = os.path.join(Config("LOG_PATH"), "app.log")
                    file_handler = RotatingFileHandler(
                        filename=_log_file,
                        maxBytes=3 * 1024 * 1024,
                        backupCount=3,
                        encoding="utf-8",
                    )
                    file_handler.setLevel(logging.DEBUG)
                    Logger._logger.addHandler(file_handler)
                    file_handler.setFormatter(formatter)

    @staticmethod
    def _apply_prefix(msg, prefix):
        return f"[{prefix}] {msg}" if prefix else msg

    @staticmethod
    def info(msg, prefix=""):
        Logger._initialize()
        Logger._logger.info(Logger._apply_prefix(msg, prefix))

    @staticmethod
    def error(msg, prefix=""):
        Logger._initialize()
        Logger._logger.error(Logger._apply_prefix(msg, prefix))

    @staticmethod
    def debug(msg, prefix=""):
        Logger._initialize()
        Logger._logger.debug(Logger._apply_prefix(msg, prefix))

    @staticmethod
    def warning(msg, prefix=""):
        Logger._initialize()
        Logger._logger.warning(Logger._apply_prefix(msg, prefix))

    @staticmethod
    def critical(msg, prefix=""):
        Logger._initialize()
        Logger._logger.critical(Logger._apply_prefix(msg, prefix))
