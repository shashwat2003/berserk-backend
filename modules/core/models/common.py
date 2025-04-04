from __future__ import annotations

from django.db import models

from common.constants import DEFAULT_ON_DELETE
from common.validators import ADDRESS_VALIDATOR
from modules.core.models.base import DropdownBase, ModelBase


class UploadFile(ModelBase):

    def upload_file(instance: UploadFile, filename: str):
        folder = (
            instance.added_by.uuid if instance.added_by is not None else "__anonymous__"
        )
        # TODO: randomize filename
        return "uploads/{0}/{1}".format(folder, filename)

    file = models.FileField(upload_to=upload_file)


# MasterDropdown Models
class MasterDropdown(DropdownBase):

    class Meta(DropdownBase.Meta):
        db_table = "core_dropdown"


# Role Models
class Role(ModelBase):
    type = models.ForeignKey(
        MasterDropdown,
        DEFAULT_ON_DELETE,
        related_name="role_types",
    )
    label = models.CharField(max_length=200)


# Organization Models
class Organization(ModelBase):
    organization = models.ForeignKey(
        MasterDropdown,
        on_delete=DEFAULT_ON_DELETE,
        related_name="organizations",
    )
    address = models.JSONField(validators=[ADDRESS_VALIDATOR], null=True)
    phone = models.CharField(max_length=12, null=True)
    email = models.EmailField(max_length=100, null=True)
    website = models.URLField(max_length=100, null=True)
    establishment_date = models.DateField(null=True)
    affiliation = models.ForeignKey(
        MasterDropdown,
        on_delete=DEFAULT_ON_DELETE,
        null=True,
        related_name="organization_affiliations",
    )


class OrganizationMedia(ModelBase):
    media_type = models.ForeignKey(
        MasterDropdown,
        on_delete=DEFAULT_ON_DELETE,
        related_name="organization_media_types",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=DEFAULT_ON_DELETE,
        related_name="medias",
    )
    media = models.ForeignKey(
        UploadFile,
        on_delete=DEFAULT_ON_DELETE,
        related_name="organization_medias",
    )


class LeftPanel(ModelBase):
    module = models.ForeignKey(
        MasterDropdown,
        on_delete=DEFAULT_ON_DELETE,
        related_name="left_panels",
    )
    role = models.ForeignKey(
        Role,
        on_delete=DEFAULT_ON_DELETE,
        related_name="left_panels",
    )
    label = models.CharField(max_length=200)
    route = models.CharField(max_length=200)
    icon = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "self",
        on_delete=DEFAULT_ON_DELETE,
        related_name="children",
        null=True,
    )
