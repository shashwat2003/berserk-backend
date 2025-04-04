from common.request import BaseRequest
from kit.views.views import BaseAPIView


class APIView(BaseAPIView):
    authentication = False

    def get(self, request: BaseRequest, id: int):
        "Test API to test dynamic routes."
        return id
