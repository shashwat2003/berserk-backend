from datetime import timedelta
from random import randint

from django.utils import timezone

from kit.views.exceptions import CustomError
from modules.core.models.common import UserOTP
from modules.core.models.user import User


class OTPService:
    EXPIRY_TIME = 5  # minutes

    @classmethod
    def generate_otp(cls, *, email: str) -> UserOTP:
        """
        Generate a 6-digit OTP and save it to the database.
        """
        if User.objects.filter(email=email).exists():
            raise CustomError("User with this email already exists.")

        otp = str(randint(100000, 999999))
        expiry_time = timezone.now() + timedelta(minutes=cls.EXPIRY_TIME)

        UserOTP.objects.filter(email=email).delete()
        user_otp = UserOTP.objects.create(email=email, otp=otp, expiry_time=expiry_time)
        return user_otp

    @classmethod
    def verify_otp(cls, *, email: str, otp: str) -> bool:
        """
        Verify the OTP for the given email.
        """
        try:
            user_otp = UserOTP.objects.get(email=email, otp=otp, is_verified=False)
        except UserOTP.DoesNotExist:
            raise CustomError("Invalid OTP or email.")

        if timezone.now() > user_otp.expiry_time:
            raise CustomError("OTP has expired.")

        user_otp.is_verified = True
        user_otp.save()

        return True
