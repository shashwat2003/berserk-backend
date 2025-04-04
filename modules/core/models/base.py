import uuid6
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone

from common.constants import DEFAULT_ON_DELETE
from modules.core.choices import StatusChoices


class BaseQuerySet(QuerySet):

    def delete(self):
        """Perform soft delete for the given query set.
        Basic behavior is derived from QuerySet.delete() method.

        Returns:
            int: The number of records that were updated.
        """
        if self.query.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with delete().")
        if self.query.distinct_fields:
            raise TypeError("Cannot call delete() after .distinct(*fields).")
        if self._fields is not None:
            raise TypeError("Cannot call delete() after .values() or .values_list()")

        return self.update(status=StatusChoices.UPDATE)

    def dangerous_delete(self):
        """To be used with extremely cation as it deletes data from db."""
        return super().delete()

    def update(self, **kwargs):
        return super().update(**kwargs, updated_at=timezone.now())


_BaseManager = models.Manager.from_queryset(BaseQuerySet)


class BaseManager(_BaseManager):
    """Base Model Manager provides the following functionality to all models:
    - Removes default deleted objects from queryset.
    - Overrides `delete` method to perform soft delete instead.
    - Provides a new `dangerous_delete` method to perform hard delete.
    """

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().exclude(status=StatusChoices.DELETE)


class ModelBase(models.Model):
    """Base Model: Contains `uuid`, `created_at`, `updated_at`, `status`"""

    BASE_MODEL_FIELDS = (
        "id",
        "created_at",
        "updated_at",
        "status",
        "added_by",
    )

    uuid = models.UUIDField(
        unique=True, default=uuid6.uuid6, editable=False, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(
        choices=StatusChoices, default=StatusChoices.CREATE
    )
    added_by = models.ForeignKey(
        "core.User",
        on_delete=DEFAULT_ON_DELETE,
        null=True,
        related_name="added_%(class)ss",
    )
    objects = BaseManager()
    unfiltered_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ("id",)
        indexes = [
            models.Index(
                fields=["status", "added_by"],
            ),
            models.Index(fields=["status", "uuid"]),
        ]


class DropdownBase(ModelBase):
    """Base Dropdown Model: Contains `label`, `parent`, `max_level`, `config`"""

    label = models.CharField(max_length=200)
    parent = models.ForeignKey(
        "self",
        DEFAULT_ON_DELETE,
        null=True,
        related_name="children",
    )
    max_level = models.IntegerField(default=0)
    config = models.SmallIntegerField(default=0)

    class Meta(ModelBase.Meta):
        abstract = True
