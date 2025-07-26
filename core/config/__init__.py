import os
from enum import StrEnum
from functools import lru_cache
from .base import get_base_dir
from .dev import DevConfig
from .prod import ProdConfig
from .test import TestConfig


class Env(StrEnum):
    prod = "prod"
    dev = "dev"
    test = "test"


def get_env():
    return os.getenv("APP_ENV") or Env.dev


@lru_cache
def get_config():
    env = get_env()
    if env != "prod":
        print(f"Environment: {env}")

    match env:
        case Env.prod:
            return ProdConfig()
        case Env.test:
            return TestConfig()
        case _:
            return DevConfig()
