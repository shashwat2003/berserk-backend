from pydantic import BaseModel


class EmployeeFixtureDataType(BaseModel):
    username: str
    email: str
    type: int
    password: str
