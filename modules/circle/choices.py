from django.db import models
from django.utils.translation import gettext_lazy as _


class CircleRoleTypeChoices(models.IntegerChoices):
    ADMIN = 1, _("Admin")
    MEMBER = 2, _("User")
