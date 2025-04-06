from typing import cast

from django.contrib.auth import authenticate

from modules.core.models import User


class AuthService:

    @classmethod
    def login(cls, *, credentials: dict[str, str]) -> User | None:
        user = authenticate(None, **credentials)
        if user is not None:
            return cast(User, user)
        return None

    @classmethod
    def generate_random_password(cls) -> str:
        """
        Generate a random password for the user.
        """
        return "ERP@123"
