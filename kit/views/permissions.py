from typing import cast

from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class APIAccessPermission(BasePermission):
    message = "You are not authorized to access this page!"
    code = status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS

    def has_permission(self, request: Request, view):
        if hasattr(view, "access_handler"):
            authentication = getattr(view, "authentication", True)
            method = cast(str, request.method).lower()
            access_handler = getattr(view, "access_handler", None)

            authentication_required = (
                authentication
                if isinstance(authentication, bool)
                else authentication.get(method, True)
            )

            if not authentication_required:  # authentication permission is turned off
                return True

            if access_handler is None:  # access handler is turned off
                return True

            if type(access_handler) == str:
                handler = getattr(view, access_handler)
                if handler is None:
                    raise ImproperlyConfigured(
                        "Handler %s, does not exists on view %s"
                        "Make sure a valid handler is present on view."
                        % (access_handler, view.__str__())
                    )
                return handler(view, request)
            elif type(access_handler) == dict:
                handler = getattr(access_handler, method)
                if handler is None:  # access handler is turned off
                    return True
                return handler(request)
            else:
                raise ImproperlyConfigured(
                    "Unknown access_handler type for %s" % (view.__str__())
                )
        return True


class APIAuthenticationPermission(BasePermission):
    message = "You are unauthenticated! Please login again!"
    code = status.HTTP_401_UNAUTHORIZED

    def has_permission(self, request: Request, view):
        authentication = getattr(view, "authentication", True)
        method = cast(str, request.method).lower()

        if not (
            authentication
            if isinstance(authentication, bool)
            else authentication.get(method, True)
        ):
            return True

        return bool(request.user and request.user.is_authenticated)
