from typing import cast

from django.apps import AppConfig
from django.conf import settings

from kit.conf.parser import ConfigParser


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.core"

    def ready(self):
        parser = cast(ConfigParser, settings.BERSERK_CONFIG_PARSER)
        parser.populate_url_patterns()
