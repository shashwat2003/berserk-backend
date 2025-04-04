from enum import IntEnum, StrEnum


class MasterDropdownEnum(StrEnum):
    MODULES = "MODULES"


class ConfigEnum(IntEnum):
    EDITABLE = 1
    DELETABLE = 3
