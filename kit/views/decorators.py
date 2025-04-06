from typing import Any, Dict, Optional, Sequence, Union

from drf_spectacular.utils import (
    OpenApiCallback,
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    _SchemaType,
    _SerializerType,
    _StrOrPromise,
)
from drf_spectacular.utils import extend_schema as og_extend_schema
from drf_spectacular.utils import inline_serializer
from rest_framework.fields import empty
from rest_framework.serializers import CharField, Field
from rest_framework.settings import api_settings

from kit.views.helpers import get_api_from_module_path

from .constants import STATUS_MAPPING
from .exceptions import CustomError, SerializerError
from .fields import NullField
from .permissions import APIAccessPermission, APIAuthenticationPermission
from .types import (
    CustomErrorResponseType,
    SerializerErrorResponseType,
    UnAuthenticatedResponseType,
    UnAuthorizedResponseType,
)


# The only way to achieve type safety + keyword arguments currently is to copy paste all parameters from base to here.
def extend_schema(
    _type: Field | None = None,
    *,
    operation_id: Optional[str] = None,
    parameters: Optional[Sequence[Union[OpenApiParameter, _SerializerType]]] = None,
    request: Any = empty,
    responses: Any = {},
    auth: Optional[Sequence[str]] = None,
    description: Optional[_StrOrPromise] = None,
    summary: Optional[_StrOrPromise] = None,
    deprecated: Optional[bool] = None,
    tags: Optional[Sequence[str]] = None,
    filters: Optional[bool] = None,
    exclude: Optional[bool] = None,
    operation: Optional[_SchemaType] = None,
    methods: Optional[Sequence[str]] = None,
    versions: Optional[Sequence[str]] = None,
    examples: Optional[Sequence[OpenApiExample]] = None,
    extensions: Optional[Dict[str, Any]] = None,
    callbacks: Optional[Sequence[OpenApiCallback]] = None,
    external_docs: Optional[Union[Dict[str, str], str]] = None,
):
    """
    Custom decorator to annotate BaseAPIView methods, in order to define the return type.
    Injects default status code with the return type.

    :param type: ReturnType of the method
    """

    def decorator(f):
        if callable(f):
            method: str = getattr(f, "__name__")
            default_response_code = STATUS_MAPPING.get(method)
            if default_response_code is None:
                return f
            api_endpoint = get_api_from_module_path(f.__module__)
            response_type = inline_serializer(
                f"{api_endpoint}{method.capitalize()}",
                {
                    "data": _type if _type is not None else NullField(),
                    "message": CharField(),
                },
            )
            return og_extend_schema(
                responses={
                    default_response_code: OpenApiResponse(
                        (response_type),
                        description="Indicates that operation was successful.",
                    ),
                    **responses,
                },
                operation_id=operation_id,
                parameters=parameters,
                request=request,
                auth=auth,
                description=description,
                summary=summary,
                deprecated=deprecated,
                tags=tags,
                filters=filters,
                exclude=exclude,
                operation=operation,
                methods=methods,
                versions=versions,
                examples=examples,
                extensions=extensions,
                callbacks=callbacks,
                external_docs=external_docs,
            )(f)
        else:
            return f

    return decorator


def extend_base_schema(cls, handler):
    """Extend the base schema, and add response types based on BaseAPIView's attributes.
    Its designed to respect all the responses dictionaries, i.e. extend_schema, which were called directly on the method.

    Args:
        handler: function that handles the request
    """
    method = getattr(handler, "__name__")

    extend_schema_params = {}

    responses = {
        CustomError.status_code: OpenApiResponse(
            CustomErrorResponseType,
            "Raised when there is a custom error, the message can be directly shown to the user.",
            [
                OpenApiExample(
                    "Example 1",
                    description="This is an example custom error, giving a custom error which has to be shown to user.",
                    value={"error": "Cannot apply leave within this range!"},
                ),
            ],
        ),
        SerializerError.status_code: OpenApiResponse(
            SerializerErrorResponseType,
            "Raised when there is a serializer error during the validation of schemas",
            [
                OpenApiExample(
                    "Foreign Key doesn't exists",
                    description="This is an example serializer error, when the foreign key doesn't exists.",
                    value={
                        "error": {
                            "author": ['Invalid pk "999" - object does not exist.']
                        }
                    },
                ),
            ],
        ),
    }

    authentication = getattr(cls, "authentication", True)

    if (
        authentication
        if type(authentication) == bool
        else authentication.get(method, True)
    ):
        responses.update(
            {
                APIAuthenticationPermission.code: OpenApiResponse(
                    UnAuthenticatedResponseType,
                    "Raised when the user is not authenticated",
                ),
                APIAccessPermission.code: OpenApiResponse(
                    UnAuthorizedResponseType,
                    "Raised when user is not allowed to access this page!",
                ),
            }
        )
    else:
        extend_schema_params["auth"] = []

    # mimic the behavior of extend_schema
    # see drf_spectacular.utils.extend_schema
    BaseSchema = (
        # explicit manually set schema or previous view annotation
        getattr(handler, "schema", None)
        # previously set schema with @extend_schema on views methods
        or getattr(handler, "kwargs", {}).get("schema", None)
        # the default
        or api_settings.DEFAULT_SCHEMA_CLASS
    )

    class ExtendedSchema(BaseSchema):
        def get_response_serializers(self):
            _responses = super().get_response_serializers() or {}
            _responses.update(responses)
            return _responses

    if not hasattr(handler, "kwargs"):
        handler.kwargs = {}
    handler.kwargs["schema"] = ExtendedSchema

    return og_extend_schema(**extend_schema_params)(handler)
