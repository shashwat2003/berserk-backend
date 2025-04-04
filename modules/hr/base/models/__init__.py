from django.db import models

from common.constants import DEFAULT_ON_DELETE
from modules.core.models import MasterDropdown, Role, User
from modules.core.models.base import DropdownBase, ModelBase


class HRDropdown(DropdownBase):
    class Meta(DropdownBase.Meta):
        db_table = "hr_dropdown"


class Employee(ModelBase):
    user = models.OneToOneField(
        User,
        on_delete=DEFAULT_ON_DELETE,
        primary_key=True,
        related_name="employees",
    )

    class Meta(ModelBase.Meta):
        ordering = ("user",)


class EmployeeRole(ModelBase):
    organization = models.ForeignKey(
        MasterDropdown,
        on_delete=DEFAULT_ON_DELETE,
        related_name="employee_role_organizations",
    )
    role = models.ForeignKey(
        Role,
        on_delete=DEFAULT_ON_DELETE,
        related_name="employees",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=DEFAULT_ON_DELETE,
        related_name="roles",
    )
