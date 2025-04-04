from modules.core.enums import ConfigEnum, MasterDropdownEnum
from modules.core.fixtures import MasterDropdownFixtureDataType
from modules.core.models import MasterDropdown

editable_and_deletable = ConfigEnum.DELETABLE | ConfigEnum.EDITABLE

master_dropdown_data = [
    MasterDropdownFixtureDataType(
        label=MasterDropdownEnum.MODULES,
        children=[
            MasterDropdownFixtureDataType(
                label="Employee",
                children=[
                    MasterDropdownFixtureDataType(
                        label='{"icon": "Test", "route": "/test"}', children=[]
                    )
                ],
            )
        ],
        max_level=2,
        config=editable_and_deletable,
    )
]


def add_master_dropdown_data():
    def helper(parent: MasterDropdown | None, dropdown: MasterDropdownFixtureDataType):
        max_level = dropdown.max_level or (parent.max_level - 1 if parent else 0)
        config = dropdown.config or (parent.config if parent else 0)
        (_dropdown, _) = MasterDropdown.objects.update_or_create(
            parent=parent,
            label=dropdown.label,
            create_defaults={
                "max_level": max_level,
                "config": config,
            },
        )

        for child in dropdown.children:
            helper(_dropdown, child)

    for dropdown in master_dropdown_data:
        helper(None, dropdown)
