from rest_framework import serializers

from common.request import BaseRequest
from kit.views.decorators import extend_schema
from kit.views.serializers import BaseModelSerializer
from kit.views.status import StatusCode
from kit.views.views import BaseAPIView
from modules.core.models.user import User
from modules.core.services.user import UserService


class RegisterPostSerializer(BaseModelSerializer):
    password = serializers.CharField()
    confirm_password = serializers.CharField()

    class Meta:
        model = User
        read_only = True
        fields = ("email", "name", "confirm_password", "password")


class APIView(BaseAPIView):
    authentication = False

    @extend_schema(RegisterPostSerializer(), request=RegisterPostSerializer)
    def post(self, request: BaseRequest):
        "Register a new user to berserk"
        input_data = RegisterPostSerializer(data=request.data)
        input_data.is_valid(raise_exception=True)

        UserService.register_user(
            **input_data.validated_data,
        )

        return input_data.data, StatusCode.X_CREATE_SUCCESSFUL("user")
