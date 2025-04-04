from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager as OGUserManager
from django.db import models

from common.constants import DEFAULT_ON_DELETE
from modules.core.choices import UserTypeChoices

from .base import BaseManager, ModelBase
from .common import UploadFile


class UserManager(BaseManager, OGUserManager):
    r"""User Manager to provide `create_user` functionality to our custom User"""

    def create_user(self, **fields):
        user = self.model(**fields)
        user.set_password(fields.get("password"))
        user.save()
        return user


class User(AbstractBaseUser, ModelBase):
    username = models.CharField(
        max_length=150,
        unique=True,
    )
    email = models.EmailField(null=True)
    type = models.SmallIntegerField(
        choices=UserTypeChoices, default=UserTypeChoices.EMPLOYEE
    )
    profile_image = models.ForeignKey(
        UploadFile,
        on_delete=DEFAULT_ON_DELETE,
        null=True,
        related_name="user_profile_images",
    )
    objects = UserManager()

    USERNAME_FIELD = "username"
