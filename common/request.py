from rest_framework.request import Request

from modules.core.models.user import User


class BaseRequest(Request):
    user: User
