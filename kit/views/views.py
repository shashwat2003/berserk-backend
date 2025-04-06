from typing import Union, cast

from pydantic import BaseModel
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView as OGAPIView

from .constants import STATUS_MAPPING
from .decorators import extend_base_schema
from .exceptions import CustomError, PermissionException
from .permissions import APIAccessPermission, APIAuthenticationPermission
from .types import APIAccessMethodType, APIAccessType, AuthenticationMethodType


class BaseAPIView(OGAPIView):
    """
    Common APIView for all views. Has two new attributes
    - `authentication`: `bool` | `kit.views.types.AuthenticationMethodType`
        - determines if authentication is required for a particular API or not.
        - open api spec also uses to this to determine additional response codes(like 409, 418 etc.).
        - defaults to `True`

    - `access_handler`: `kit.views.types.APIAccessType` | `kit.views.types.APIAccessMethodType`
        - determines which function to run in order validate if the user has access to particular api.
        - if set to string, it looks up the view for that particular function name, and calls it.
        - the function receives one arguments:
            - `request`: `rest_framework.request.Request`, the incoming request object.
        - this function must return True or False, to determine api access.
        - defaults to 'validate_view'

    Raises:
    - `PermissionException`: `kit.views.exception.PermissionException`
        - handled by `kit.views.views.exception_handler`.
        - raises `403`, `FORBIDDEN` by default (can be overridden by `message` and `code` on `rest_framework.permissions.BasePermission` class) if the user doesn't have permission to access the API.
    """

    permission_classes = [APIAuthenticationPermission, APIAccessPermission]
    authentication: Union[bool, AuthenticationMethodType] = True
    access_handler: Union[APIAccessType, APIAccessMethodType, None] = "validate_view"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for method in cls.http_method_names:
            handler = getattr(cls, method, None)
            if handler is not None and callable(handler):
                handler = extend_base_schema(cls, handler)
                setattr(cls, method, handler)

    def permission_denied(self, request, message=None, code=None):
        """
        If request is not permitted, determine what kind of exception to raise.
        Overriding default behavior because it was not customizable, always raising
        `rest_framework.exceptions.NotAuthenticated`, not respecting `message` or `code` (in case of `401`, `UNAUTHORIZED`).
        """
        raise PermissionException(detail=message, code=code)

    def finalize_response(self, request: Request, response, *args, **kwargs):
        "Build up the final response based on the items returned from method functions."

        if isinstance(response, (tuple)):
            match len(response):
                case 1:
                    data = response[0]
                    message = ""
                    status_code = None
                case 2:
                    data, message = response
                    status_code = None
                case 3:
                    data, message, status_code = response
                case _:
                    raise ValueError("Invalid response tuple length")

            if isinstance(data, BaseModel):
                data = data.model_dump()
            elif isinstance(data, Serializer):
                data = data.data

            default_response_code = (
                STATUS_MAPPING.get(cast(str, request.method).lower())
                or status.HTTP_200_OK
            )
            response = Response(
                {"data": data, "message": message},
                status=default_response_code if status_code is None else status_code,
            )
        elif not isinstance(response, Response):
            raise ValueError(
                "Can only return Response or tuple of (data, message, status_code)!"
            )
        return super().finalize_response(request, response, *args, **kwargs)

    def fail(self, message: str):
        "Raises a CustomError"
        raise CustomError(message)

    def validate_view(self, _: Request):
        "Override this method in sub classes to determine api access"
        return True
