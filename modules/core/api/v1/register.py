from rest_framework import serializers

from common.request import BaseRequest
from kit.views.decorators import extend_schema
from kit.views.serializers import BaseModelSerializer
from kit.views.status import StatusCode
from kit.views.views import BaseAPIView
from modules.core.models.user import User
from modules.core.services.otp import OTPService
from modules.core.services.user import UserService


class RegisterPostSerializer(BaseModelSerializer):
    password = serializers.CharField()
    confirm_password = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    class Meta:
        model = User
        read_only = True
        fields = ("email", "name", "confirm_password", "password", "otp")


class APIView(BaseAPIView):
    authentication = False

    @extend_schema(request=RegisterPostSerializer)
    def post(self, request: BaseRequest):
        "Register a new user to berserk"
        input_data = RegisterPostSerializer(data=request.data)
        input_data.is_valid(raise_exception=True)

        OTPService.verify_otp(
            email=input_data.validated_data.get("email"),
            otp=input_data.validated_data.pop("otp"),
        )

        UserService.register_user(
            **input_data.validated_data,
        )

        return None, StatusCode.X_CREATE_SUCCESSFUL("user")
