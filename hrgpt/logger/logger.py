import enum
import logging
import os.path
import sys

from hrgpt.config.config import LoggingConfiguration
from hrgpt.utils.path_utils import get_repo_root_path


class LoggerType(enum.StrEnum):
    APPLICATION = enum.auto()
    ROOT = enum.auto()


class LoggerFactory:
    logger_dict: dict[LoggerType, logging.Logger] = {}

    @classmethod
    def get_application_name(cls) -> str:
        return os.path.basename(get_repo_root_path()).lower()

    @classmethod
    def initialize_loggers(cls, config: LoggingConfiguration):
        for logger_identifier in config.loggers_to_disable_propagation:
            logger = logging.getLogger(logger_identifier)
            logger.propagate = False
        for logger_type in LoggerType:
            if logger_type == LoggerType.APPLICATION:
                logger = logging.getLogger(cls.get_application_name())
                logger.setLevel(logging.getLevelName(config.application_logging_level))
            else:
                logger = logging.getLogger()
                logger.setLevel(logging.getLevelName(config.root_logging_level))
            logger.handlers.clear()
            logger.propagate = False
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(logging.NOTSET)
            stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setLevel(logging.WARNING)
            log_format = logging.Formatter("[%(levelname)s/%(name)s]: %(message)s")
            stdout_handler.setFormatter(log_format)
            stderr_handler.setFormatter(log_format)
            logger.addHandler(stdout_handler)
            logger.addHandler(stderr_handler)
            logger.addFilter(lambda record: record.name != logger.name)
            cls.logger_dict[logger_type] = logger

    @classmethod
    def get_logger(
        cls, logger_type: LoggerType = LoggerType.APPLICATION
    ) -> logging.Logger:
        if logger_type not in cls.logger_dict:
            raise RuntimeError
        return cls.logger_dict[logger_type]
