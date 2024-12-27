import os

import yaml

from helpers.errors import ConfigurationError

_config_path = os.path.join("config", "config.yml")


class _ConfigMeta(type):
    _config = None

    def initialize(cls):
        if cls._config is None:
            if not os.path.exists(_config_path):
                raise ConfigurationError(
                    f"Configuration file not found: {_config_path}"
                )
            with open(_config_path, "r", encoding="utf-8") as file:
                cls._config = yaml.safe_load(file)

    def __call__(cls, config_name):
        cls.initialize()
        return cls._config.get(config_name)


class Config(metaclass=_ConfigMeta):
    pass
