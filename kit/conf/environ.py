from django.conf import settings
from pydantic import BaseModel, ConfigDict, Field

REPLACEMENTS = {"DATABASE": "DB", "RABBITMQ": "rmq"}


def alias_generator(string: str) -> str:
    alias = string
    for original, replacement in REPLACEMENTS.items():
        alias = alias.replace(original, replacement)
    alias = alias.lower()
    return alias


class BaseEnviron(BaseModel):
    model_config = ConfigDict(alias_generator=alias_generator)

    IS_PROD: bool
    SECRET_KEY: str = Field(alias="key")
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASS: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASS: str


def get_environ(config: dict[str, str] | None) -> BaseEnviron:
    if config is None:
        config = getattr(settings, "BERSERK_CONFIG_PARSER")
    return BaseEnviron.model_validate(config.get("settings", {}), by_alias=True)
