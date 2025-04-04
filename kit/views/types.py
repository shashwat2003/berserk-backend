from collections.abc import Callable
from typing import Literal, TypeAlias, TypedDict, Union

from pydantic import BaseModel
from rest_framework.request import Request

APIAccessType: TypeAlias = Union[Callable[[Request], bool], str]


class APIAccessMethodType(TypedDict, total=False):
    get: APIAccessType
    post: APIAccessType
    put: APIAccessType
    delete: APIAccessType


class AuthenticationMethodType(TypedDict, total=False):
    get: bool
    post: bool
    put: bool
    delete: bool


class DynamicKeysType(TypedDict):
    name: str
    source: str
    type: Literal["int", "str", "float", "bool"]


class CascaderType(TypedDict):
    name: str
    field: str


class RecursiveType(CascaderType):
    index: int


class PaginationConfigType(TypedDict):
    run_before_pagination: str
    run_after_pagination: str


class UnAuthenticatedResponseType(BaseModel):
    msg: Literal["You are unauthenticated! Please login again!"]


class UnAuthorizedResponseType(BaseModel):
    msg: Literal["You are not authorized to access this page!"]


class CustomErrorResponseType(BaseModel):
    msg: str


class SerializerErrorResponseType(BaseModel):
    detail: list[str]
