import os

import yaml
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .config import Config


class ConfigParser:
    """This class is used for parsing the config for berserk.

    Attributes:
    - `CONFIG_FILE`: name of the config file to be parsed(should be present in root of the project)
    - `APPS_KEY_LIST`: defines the list of application that should be picked from `config.settings`
    - `parsed_yaml_config`: the result of `yaml.safe_load` on `CONFIG_FILE`
    - `config`: a valid config object of class `config.config.Config`
    """

    CONFIG_FILE = "berserk-config.yaml"
    APPS_KEY_LIST = ["DJANGO_APPS", "THIRD_PARTY_APPS", "NON_PROD_APPS", "PROD_APPS"]
    parsed_yaml_config: dict
    config: Config | None
    initialized = False

    def __init__(self) -> None:
        """Initializes a new `ConfigParser`. Checks if the config file exists, and then parses it."""

        config_file = os.path.join(self.CONFIG_FILE)
        if not os.path.isfile(config_file):
            ImproperlyConfigured(
                "Config file %s, does not exists in current path"
                "Make sure a valid berserk config file exists." % (self.CONFIG_FILE)
            )

        if not ConfigParser.initialized:
            with open(config_file, "r") as file:
                try:
                    ConfigParser.parsed_yaml_config = yaml.safe_load(file)
                except yaml.YAMLError:
                    ImproperlyConfigured(
                        "There was a yaml parsing error in loading %s"
                        "Make sure a valid berserk config file exists."
                        % (self.CONFIG_FILE)
                    )

        ConfigParser.initialized = True

    def build_config(self):
        """Create and set `config` attribute from `parsed_yaml_config`.
        - Sets the `INSTALLED_APPS`, `berserk_CONFIG` for `config.settings`
        - Sets `urlpatterns` for `config.urls`
        """

        self.config = Config(self.parsed_yaml_config)
        installed_apps = [
            app for key in self.APPS_KEY_LIST for app in getattr(settings, key, [])
        ]
        installed_apps.extend(self.config.installed_apps)
        setattr(settings, "BERSERK_CONFIG_PARSER", self)
        setattr(settings, "BERSERK_CONFIG", self.config)
        setattr(settings, "INSTALLED_APPS", installed_apps)

    def populate_url_patterns(self):
        from config import urls

        urlpatterns = getattr(urls, "urlpatterns", [])
        urlpatterns += self.config.urlpatterns
        setattr(urls, "urlpatterns", urlpatterns)
