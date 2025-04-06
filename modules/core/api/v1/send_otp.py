from common.request import BaseRequest
from kit.views.decorators import extend_schema
from kit.views.serializers import BaseModelSerializer
from kit.views.status import StatusCode
from kit.views.views import BaseAPIView
from modules.core.models.common import UserOTP
from modules.core.services.otp import OTPService


class SendOTPPostBodySerializer(BaseModelSerializer):

    class Meta:
        model = UserOTP
        fields = ("email",)


class APIView(BaseAPIView):
    authentication = False

    @extend_schema(request=SendOTPPostBodySerializer)
    def post(self, request: BaseRequest):
        serializer = SendOTPPostBodySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        OTPService.generate_otp(**serializer.validated_data)

        return None, StatusCode.X_SENT_SUCCESSFUL("otp")
