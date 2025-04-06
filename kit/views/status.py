from typing import Protocol


class DerivedStatusCallable(Protocol):
    def __call__(self, *args: str) -> str: ...


def derived_status_code(text: str) -> DerivedStatusCallable:
    def inner_func(*args: str) -> str:
        return text.format(*args).capitalize()

    return inner_func


class StatusCode:
    # Use them rarely
    NOT_FOUND = "No data found!"
    CREATE_SUCCESSFUL = "Created Successfully!"
    UPDATE_SUCCESSFUL = "Updated Successfully!"
    DELETE_SUCCESSFUL = "Deleted Successfully!"

    # Use them frequently
    X_NOT_FOUND = derived_status_code("{0} not found!")
    X_UUID_NOT_EXIST = derived_status_code("Record ({0}) does not exists!")
    X_CREATE_SUCCESSFUL = derived_status_code("{0} created successfully!")
    X_UPDATED_SUCCESSFUL = derived_status_code("{0} updated successfully!")
    X_DELETE_SUCCESSFUL = derived_status_code("{0} deleted successfully!")
    X_SENT_SUCCESSFUL = derived_status_code("{0} sent successfully!")
