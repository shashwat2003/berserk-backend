from modules.core.choices import UserTypeChoices
from modules.core.models import User
from modules.hr.base.fixtures import EmployeeFixtureDataType

employee_data = [
    EmployeeFixtureDataType(
        username="007",
        email="core@kubejen.com",
        type=UserTypeChoices.EMPLOYEE,
        password="ERP@123",
    )
]


def add_employee_data():
    for employee in employee_data:
        (_user, _) = User.objects.update_or_create(
            username=employee.username,
            defaults={
                "email": employee.email,
                "type": employee.type,
            },
        )
        _user.set_password(employee.password)
        _user.save()
