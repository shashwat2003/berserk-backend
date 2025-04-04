import asyncio
import os
from functools import cached_property
from importlib import import_module
from typing import Dict, Generator, List

from django.apps import AppConfig
from django.conf import settings
from django.urls import URLPattern, URLResolver, include, path
from django.utils.module_loading import module_has_submodule

from .helpers import deep_merge
from .types import ModuleConfig, ModuleSettings, SubModuleType, URLSType

DEFAULT_MODULES = ModuleConfig.validate_python(
    {
        "core": {"api_versions": ["v1"]},
        "hr": {"submodules": {"base": {"api_versions": ["v1"]}}},
    }
)

# updated below because settings need to be initialized before using
AVAILABLE_API_VERSIONS: list[str] = []


class Module:
    """This class is used as a blueprint for a `Module` object.

    Attributes:
    - `name`: name of the module
    - `submodules`: list of the name of all submodules
    - `api_versions`: list of the name of all api_versions
    - `app_configs`: a dict containing module wise `django.apps.AppConfig` object
    - `urls`: a dict containing module wise `urlpatterns`
    """

    name: str
    submodules: Dict[str, SubModuleType]
    settings: ModuleSettings
    api_versions: List[str]

    app_configs: dict[str, AppConfig]
    urls: dict[str, dict[str, URLSType]]

    def __init__(self, name: str, **kwargs) -> None:
        """Initializes a new `Module` object

        Args:
            name (str): name of the module
        """
        self.name = name
        self.submodules = kwargs.get("submodules", {})
        self.settings = kwargs.get("settings", {})
        self.api_versions = kwargs.get("api_versions", [])

        self.app_configs = {}
        self.urls = {}

    def populate(self) -> None:
        """Populates `app_configs` and fetch api wise module name for populating urls in future."""
        if self.settings.get("standalone", False):
            module_path = "modules.%s" % (self.name)
            app_config = AppConfig.create(module_path)
            self.app_configs[module_path] = app_config
            for api_version in self.api_versions:
                self.fetch_urls(module_path, app_config, api_version)
        else:
            for submodule, config in self.submodules.items():
                module_path = "modules.%s.%s" % (self.name, submodule)
                app_config = AppConfig.create(module_path)
                self.app_configs[module_path] = app_config
                for api_version in config.get("api_versions"):
                    self.fetch_urls(module_path, app_config, api_version)

    def fetch_urls(
        self, module_path: str, app_config: AppConfig, api_version: str
    ) -> None:
        """Fetch `urlpatterns` for each module.

        Args:
            module_path (str): full path of the module
            app_config (AppConfig): `django.apps.AppConfig` object for the module
        """
        self.urls.setdefault(api_version, {})
        self.urls[api_version].setdefault(
            module_path,
            {"resolver": None, "views_module_name": None},
        )

        api_module_name = "api.%s" % (api_version)
        if module_has_submodule(app_config.module, api_module_name):
            views_module_name = "%s.%s" % (
                module_path,
                api_module_name,
            )
            self.urls[api_version][module_path]["views_module_name"] = views_module_name

    def populate_urls(self):
        """Populates `urls` for each module api version wise.
        Module here refers to '.' separated path of submodule/module.
        """
        for api_version, modules in self.urls.items():
            for module, config in modules.items():
                if config.get("views_module_name") is None:
                    continue
                app_config = self.app_configs.get(module)
                url_patterns = []
                self._make_urls(config.get("views_module_name"), None, url_patterns)
                prefix = (
                    f"/{getattr(app_config, "url_prefix")}/"
                    if hasattr(app_config, "url_prefix")
                    else f"/{app_config.label.replace(".", "/")}/"
                )
                self.urls[api_version][module]["resolver"] = path(
                    prefix, include(url_patterns)
                )

    # magic happens here :-)
    def _make_urls(
        self, views_module_name: str, parent_url: str | None, url_patterns: list
    ):
        """Recursively iterate through modules and submodules views to generate url patterns and resolvers

        Args:
            views_module_name (str): '.' separated path of the module
            parent_url (str | None): parent url in case of nested folders. Initially None.
            url_patterns (list): for recursively save the urlpatterns
        """
        base_dir = os.path.join(settings.BASE_DIR, views_module_name.replace(".", "/"))
        for item in os.listdir(base_dir):
            is_file = os.path.isfile(os.path.join(base_dir, item))

            if is_file:
                if not item.endswith(".py") or (
                    item.startswith("_") and item != "__init__.py"
                ):  # skip extra files
                    continue

                if item == "__init__.py":
                    view_module = import_module("%s" % (views_module_name))
                else:
                    view_module = import_module(
                        "%s.%s" % (views_module_name, item.replace(".py", ""))
                    )
                if hasattr(view_module, "APIView"):
                    url_prefix = getattr(view_module, "url_prefix", None)
                    prefix = "%s%s" % (
                        f"{parent_url}/" if parent_url is not None else "",
                        (
                            url_prefix
                            if url_prefix is not None
                            else (
                                "" if item == "__init__.py" else item.replace(".py", "")
                            )
                        ),
                    )
                    if prefix != "" and prefix[-1] != "/":
                        prefix += "/"
                    url_patterns.append(
                        path(prefix, getattr(view_module, "APIView").as_view())
                    )

            else:
                if item.startswith("_"):  # skip extra files
                    continue
                self._make_urls(
                    f"{views_module_name}.{item}",
                    f"{f"{parent_url}/" if parent_url is not None else ""}{item}",
                    url_patterns,
                )


class Config:
    """This class is used for generating and validating the config file for berserk.

    Attributes:
    - `modules`: a dictionary of module path as key and an object of `Module`
    """

    modules: dict[str, Module]

    def __init__(self, parsed_config: dict) -> None:
        """Initialize a new `Config` object.

        Args:
            parsed_config (dict): parsed dictionary of the config
        - Sets `modules` attribute of the current object
        """
        self.modules = {}
        modules_config = ModuleConfig.validate_python(parsed_config.get("modules", {}))

        modules_config = deep_merge(DEFAULT_MODULES, modules_config)
        modules = list(modules_config.keys())

        for module in modules:
            module_config = modules_config.get(module, {})
            _module = Module(module, **module_config)
            _module.populate()
            self.modules[module] = _module

    @cached_property
    def installed_apps(self) -> List[AppConfig]:
        """Cached `INSTALLED_APPS` built from config

        Returns:
            List[AppConfig]: List of all `INSTALLED_APPS` that needs to be substituted in `django.conf.settings`
        """
        return [
            app_config
            for module in self.modules.values()
            for app_config in module.app_configs.values()
        ]

    @cached_property
    def urlpatterns(self) -> list:
        """Cached `urlpatterns` built from config

        Returns:
            list: List of all `urlpatterns` including `api_versions` that needs to be substituted in `config.urls`
        """
        [module.populate_urls() for module in self.modules.values()]
        AVAILABLE_API_VERSIONS = [
            api_version[0]
            for api_version in os.walk(os.path.join(settings.BASE_DIR, "config/api"))
            if os.path.basename(api_version[0]) != "__pycache__"
        ]
        urlpatterns: List[URLResolver] = []
        for api_folder in AVAILABLE_API_VERSIONS[1:]:
            api_version = api_folder.split("/")[-1]
            urlpatterns.append(
                path(
                    api_version,
                    include(
                        [
                            sub_module["resolver"]
                            for module in self.modules.values()
                            for sub_module in module.urls.get(api_version).values()
                            if sub_module["resolver"] is not None
                        ]
                    ),
                )
            )

        asyncio.run(self._save_urls(urlpatterns))

        return urlpatterns

    async def _save_urls(self, urlpatterns: List[URLResolver]):
        """Async function to save the urls in a _routes.py.

        Args:
            urlpatterns (List[URLResolver]): urlpatterns to be saved
        """
        _routes = ""
        for url_info in self._list_urls(urlpatterns):
            url = "".join([info["url"] for info in url_info])
            module = url_info[-1]["module"]

            _routes += f"""
'''{url}'''
'''{module}.APIView'''
"""

        with open(
            os.path.join(settings.BASE_DIR, "_routes.py"),
            "w",
        ) as f:
            f.write(
                f"""# This file is auto generated by kit. Do not edit this file manually.
# Python extension is required in order to Cmd + Click to navigate to view class.
"""
            )
            f.write(_routes)

    def _list_urls(
        self,
        urlpatterns: List[URLResolver],
        resolved_list: List[Dict[str, str]] | None = None,
    ) -> Generator[List[Dict[str, str]]]:
        """Convert urlpatterns in form of list of [{url: str, module: str}]
        Reference: https://stackoverflow.com/a/54531546

        Args:
            urlpatterns (List[URLResolver]): urlpatterns to be converted
            resolved_list (List[Dict[str, str]] | None, optional): Used for recursive calls initially None.
        """
        if resolved_list is None:
            resolved_list = []
        if not urlpatterns:
            return
        url = urlpatterns[0]
        if isinstance(url, URLPattern):
            yield resolved_list + [
                {
                    "url": str(url.pattern),
                    "module": url.callback.__dict__.get("view_class").__dict__.get(
                        "__module__"
                    ),
                }
            ]
        elif isinstance(url, URLResolver):
            yield from self._list_urls(
                url.url_patterns,
                resolved_list
                + [
                    {
                        "url": str(url.pattern),
                    }
                ],
            )
        yield from self._list_urls(urlpatterns[1:], resolved_list)
