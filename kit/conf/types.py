from typing import Dict, List, NotRequired, TypeAlias, TypedDict

from django.urls import URLResolver
from pydantic import TypeAdapter

APIVersionsType: TypeAlias = List[str]


class SubModuleType(TypedDict):
    api_versions: NotRequired[APIVersionsType]


class ModuleSettings(TypedDict):
    standalone: NotRequired[bool]


class ModuleType(TypedDict):
    api_versions: NotRequired[APIVersionsType]
    submodules: NotRequired[Dict[str, SubModuleType]]
    settings: NotRequired[ModuleSettings]


ModuleConfigType: TypeAlias = Dict[str, ModuleType]

ModuleConfig = TypeAdapter(ModuleConfigType)


class URLSType(TypedDict):
    resolver: URLResolver | None
    views_module_name: str | None
