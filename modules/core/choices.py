from django.db import models
from django.utils.translation import gettext_lazy as _


class StatusChoices(models.IntegerChoices):
    DELETE = 0, _("Deleted")
    CREATE = 1, _("Created")
    UPDATE = 2, _("Updated")


class UserTypeChoices(models.IntegerChoices):
    USER = 1, _("User")
