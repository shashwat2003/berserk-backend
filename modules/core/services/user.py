from kit.views.exceptions import CustomError
from modules.core.models.user import User


class UserService:

    @classmethod
    def register_user(
        cls, *, email: str, password: str, confirm_password: str, name: str
    ) -> User:
        """
        Register a new user with the given email, password, and name.
        """
        if password != confirm_password:
            raise CustomError("Passwords do not match!")
        if User.objects.filter(email=email).exists():
            raise CustomError("A user with this email already exists!")

        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
        )

        return user
