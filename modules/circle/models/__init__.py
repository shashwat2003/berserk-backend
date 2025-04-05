# Circle Models
from django.db import models

from common.constants import DEFAULT_ON_DELETE
from modules.circle.choices import CircleRoleTypeChoices
from modules.core.models.base import ModelBase
from modules.core.models.user import User


class Circle(ModelBase):
    name = models.CharField(max_length=50)
    created_date = models.DateField(null=True)


class CircleMember(ModelBase):
    circle = models.ForeignKey(
        Circle,
        on_delete=DEFAULT_ON_DELETE,
        related_name="circle_members",
    )
    user = models.ForeignKey(
        User,
        on_delete=DEFAULT_ON_DELETE,
        related_name="circle_members",
    )
    role = models.IntegerField(
        choices=CircleRoleTypeChoices,
        default=CircleRoleTypeChoices.MEMBER,
    )
    joined_date = models.DateField(null=True)
