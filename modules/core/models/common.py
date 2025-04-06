from __future__ import annotations

from django.db import models

from .base import DropdownBase, ModelBase


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


class UserOTP(ModelBase):

    email = models.EmailField(max_length=255)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    expiry_time = models.DateTimeField()
