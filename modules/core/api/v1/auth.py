import base64

from django.contrib.auth import login
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter
from rest_framework import serializers

from common.request import BaseRequest
from kit.views.decorators import extend_schema
from kit.views.views import BaseAPIView
from modules.core.services.auth import AuthService


class UserLoginDetailSerializer(serializers.Serializer):
    username = serializers.CharField()


class APIView(BaseAPIView):
    authentication = {"post": False}

    @extend_schema(UserLoginDetailSerializer())
    def get(self, request: BaseRequest):
        "Retrieve user details for the logged in user."
        return UserLoginDetailSerializer(request.user)

    @extend_schema(
        UserLoginDetailSerializer(),
        request={},
        parameters=[
            OpenApiParameter(
                name="Authorization",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description='Base64 encoded ":" separated username & password.',
                examples=[
                    OpenApiExample(
                        "Example",
                        summary="Example header for authentication",
                        description="Username: 00007, Password: ERP@123",
                        value="Basic MDAwMDc6RVJQQDEyMw==",
                    )
                ],
            ),
        ],
    )
    def post(self, request: BaseRequest):
        "Login the user with the provided credentials."
        credentials = self.decrypt_auth(request)
        user = AuthService.login(credentials=credentials)
        if user is not None:
            login(request, user)
            return UserLoginDetailSerializer(request.user)

        self.fail("Credentials were incorrect!")

    def decrypt_auth(self, request: BaseRequest):
        try:
            header: str = request.META["HTTP_AUTHORIZATION"]
            decrypted_header = bytes(
                base64.b64decode(header.replace("Basic", "").strip())
            ).decode()
            (username, password) = decrypted_header.split(":")
        except:
            self.fail("Invalid header sent!")

        return {"username": username, "password": password}
