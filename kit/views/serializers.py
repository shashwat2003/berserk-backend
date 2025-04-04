from functools import cached_property
from typing import List, Literal, Union

from django.conf import settings
from django.core.paginator import InvalidPage, Page, Paginator
from django.db.models.query import QuerySet
from rest_framework import serializers
from rest_framework.request import Request

from common.functions import (
    getattr_recursive,
    recursive_parent_list,
    recursive_parent_lookup,
)

from .constants import FIELDS_MAPPING
from .types import CascaderType, DynamicKeysType, PaginationConfigType, RecursiveType


class BaseModelListSerializer(serializers.ListSerializer):
    """A customized `rest_framework.serializers.ListSerializer` with implemented `update` and `get_paginated_response` method.
    - `update`:
        - Call the method defined as `update_list_method` on child serializer.
        - If it is set as "default" then execute `update_list`.
    - `get_paginated_response`:
        - Generate paginated response based on child serializer
    """

    def update(self, instance, validated_data):
        update_method = getattr(self.child, "update_list_method", None)
        if update_method == "default":
            return self.update_list(instance, validated_data)
        elif hasattr(self.child, update_method):
            return (getattr(self.child, update_method))(instance, validated_data)

        return super().update()

    def update_list(self, instance, validated_data):
        # Get primary key field name.
        pk = self.child.Meta.model._meta.pk.name
        print(validated_data)
        # Maps for pk->instance and pk->data item.
        entry_mapping = {getattr(entry, pk): entry for entry in instance}
        data_mapping = {
            validated_data[index].get(pk, -(index + 1)): validated_data[index]
            for index in range(len(validated_data))
        }

        # Perform creations and updates accordingly
        operations = []
        for entry_id, data in data_mapping.items():
            print("entry__id>>", entry_id)
            entry = entry_mapping.get(entry_id, None)
            if entry is None:
                print("Create")
                operations.append(self.child.create(data))
            else:
                print("update")
                operations.append(self.child.update(entry, data))

        # Perform deletions of all objects which are not in validated_data
        for entry_id, entry in entry_mapping.items():
            if entry_id not in data_mapping:
                print("deleted >> ", entry_id)
                entry.status = "DELETE"
                entry.save()
        return operations

    def get_paginated_response(self, request: Request | None = None):
        pagination_config: PaginationConfigType | None = getattr(
            self.child, "pagination_config"
        )

        if pagination_config is None:
            raise AssertionError("pagination_config is not present in the serializer!")

        if request is None:
            request = getattr(self.child, "request")

        if hasattr(self.child, pagination_config["run_before_pagination"]):
            getattr(self.child, pagination_config["run_before_pagination"])(
                getattr(self.child, "instance")
            )

        paginator = Paginator(
            getattr(self.child, "instance"),
            request.query_params.get(getattr(settings, "PAGE_LIMIT_PARAM"), 10),
        )
        try:
            self.instance = paginator.page(
                request.query_params.get(getattr(settings, "PAGE_NUMBER_PARAM"), 1)
            )
        except InvalidPage:
            pass

        if hasattr(self.child, pagination_config["run_after_pagination"]):
            getattr(self.child, pagination_config["run_after_pagination"])(
                self.instance
            )

        return {
            "data": self.data,
            "count": paginator.count,
            "columns": {
                "searchable": (
                    getattr(self.child, "searchable_columns")
                    if hasattr(self.child, "searchable_columns")
                    else []
                ),
                "sortable": (
                    hasattr(self.child, "searchable_columns")
                    if hasattr(self.child, "searchable_columns")
                    else []
                ),
            },
        }

    def to_representation(self, data):
        return super().to_representation(
            data.object_list if isinstance(data, Page) else data
        )


class BaseModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    Use this serializer to get Dynamic fields.
    Pass `request` with `rest_framework.request.Request` object, and
    `sort=True` for sorting and `search=True` for searching.
    """

    update_list_method: Union[Literal["default"], str] = "default"
    dynamic_keys: List[Union[str, DynamicKeysType]] = []
    cascader: List[Union[str, CascaderType]] = []
    recursive: List[Union[str, RecursiveType]] = []
    file_fields: List[Union[str, CascaderType]] = []
    pagination_config: PaginationConfigType = {
        "run_before_pagination": "run_before_pagination",
        "run_after_pagination": "run_after_pagination",
    }
    instance: QuerySet

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        exclude = kwargs.pop("exclude", None)
        nest = kwargs.pop("nest", None)
        self.Meta.list_serializer_class = (
            self.Meta.list_serializer_class
            if hasattr(self.Meta, "list_serializer_class")
            else BaseModelListSerializer
        )
        self.search = kwargs.pop("search", False)
        self.sort = kwargs.pop("sort", False)
        self.request = kwargs.pop("request", None)

        if nest is True:
            self.Meta.depth = 1

        super(BaseModelSerializer, self).__init__(*args, **kwargs)

        for field in self.dynamic_keys:
            isDict = isinstance(field, dict)
            field_type = (
                (
                    "int"
                    if field.get("source").split(".")[-1] == "id"
                    # or field.get("type") == "int"
                    else field.get("type", "str")
                )
                if isDict
                else "str"
            )

            self.fields.update(
                {
                    field.get("name") if isDict else field.replace(".", "_"): (
                        getattr(serializers, FIELDS_MAPPING.get(field_type))
                    )(
                        source=field.get("source") if isDict else field,
                        read_only=True,
                    )
                }
            )

        if (self.search or self.sort) and self.request is None:
            raise AssertionError(
                "Request object is mandatory when search/sort is True!"
            )

        if self.search:
            field = self.request.query_params.get(settings.SEARCH_FIELD_PARAM, "")
            query = self.request.query_params.get(settings.SEARCH_QUERY_PARAM, "")
            print(field, query)
            if field != "" and query != "":
                if field in self.searchable_columns:
                    self.instance = self.search_field(field, query)
        if self.sort:
            sorts = self.request.query_params.get(settings.SORT_QUERY_PARAM, "")
            if sorts != "":
                self.instance = self.sort_fields(sorts.split(","))

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name)

    def search_field(self, field_name: str, query: str):
        field = self.fields.get(field_name)

        if isinstance(field, serializers.SerializerMethodField):
            search_func = getattr(self, "search_" + field_name, None)
            if callable(search_func):
                return search_func(self.instance, query)
            else:
                return self.instance

        lookup = self.generate_lookup(field, field_name)
        print(lookup)
        if isinstance(field, serializers.CharField):
            lookup += "__icontains"

        if isinstance(field, serializers.DateTimeField):
            lookup += "__date"
        print(self.instance.filter(**{lookup: query.strip()}), lookup)
        try:
            return self.instance.filter(**{lookup: query.strip()})
        except:
            return self.instance

    def sort_fields(self, sorts: List[str]):
        sortable_fields_list = []
        for sort in sorts:
            if sort != "":
                sort_type = "-" if sort[0] == "-" else ""
                field_name = sort[1:]

                if field_name not in self.sortable_columns:
                    continue

                field = self.fields.get(field_name)
                if isinstance(field, serializers.SerializerMethodField):
                    sort_func = getattr(self, "sort_" + field_name, None)
                    if callable(sort_func):
                        # TODO: THINK OF A SOLUTION
                        pass
                    else:
                        continue

                sortable_fields_list.append(
                    "{0}{1}".format(sort_type, self.generate_lookup(field, field_name))
                )
        try:
            return self.instance.order_by(*sortable_fields_list)
        except:
            return self.instance

    @cached_property
    def recursive_columns(self):
        columns = {}
        for field in self.recursive:
            isStr = isinstance(field, str)
            field_name = field if isStr else field.get("name")
            if field_name in self.fields.keys():
                columns.update({field_name: field if not isStr else None})
        return columns

    @cached_property
    def searchable_columns(self):
        columns = []
        for field in self.fields.keys():
            if isinstance(self.fields.get(field), serializers.SerializerMethodField):
                if not hasattr(self, "search_%s" % field):
                    continue
            columns.append(field)
        return columns

    @cached_property
    def sortable_columns(self):
        columns = []
        for field in self.fields:
            if isinstance(self.fields.get(field), serializers.SerializerMethodField):
                if not hasattr(self, "sort_%s" % field):
                    continue
            columns.append(field)
        return columns

    def get_parent_list(self, instance, field, field_name):
        source = (
            getattr(self.fields.get(field_name), "source")
            if getattr(self.fields.get(field_name), "source") != ""
            else field_name
        )
        return recursive_parent_list(
            getattr_recursive(
                instance,
                source,
            ),
            "id" if isinstance(field, str) else field.get("field"),
        )

    def generate_lookup(self, field, field_name):
        source = (
            getattr(field, "source") if getattr(field, "source") != "" else field_name
        )
        lookup = ""
        if field_name in self.recursive_columns:
            instance = self.instance.first()
            if instance:
                recursive_options = self.recursive_columns.get(field_name)
                lookup = "{parent}__{field}".format(
                    parent="__".join(
                        recursive_parent_lookup(
                            getattr_recursive(
                                instance,
                                source,
                            ),
                        )[
                            (
                                2
                                if recursive_options is not None
                                else recursive_options.get("index", 1) + 1
                            ) :
                        ]
                    ),
                    field=(
                        "id"
                        if recursive_options is None
                        else recursive_options.get("field")
                    ),
                )
        return (
            "%s__%s" % (source.replace(".", "__"), lookup)
            if lookup != ""
            else source.replace(".", "__")
        )

    def to_representation(self, instance):
        fields = super().to_representation(instance)
        for field in self.cascader:
            field_name = field if isinstance(field, str) else field.get("name")
            if field_name in fields.keys():
                parents = self.get_parent_list(instance, field, field_name)
                fields[field_name] = parents[1:] if len(parents) > 0 else []
        for field in self.file_fields:
            isStr = isinstance(field, str)
            field_name = field if isStr else field.get("name")
            if field_name in fields.keys():
                fields[field_name] = (
                    {
                        "url": getattr(
                            getattr(
                                getattr_recursive(
                                    instance, field if isStr else field.get("field")
                                ),
                                "file",
                            ),
                            "url",
                        ),
                        "id": getattr(
                            getattr_recursive(
                                instance, field if isStr else field.get("field")
                            ),
                            "id",
                        ),
                    }
                    if getattr_recursive(
                        instance, field if isStr else field.get("field")
                    )
                    else None
                )
        for field in self.recursive:
            isStr = isinstance(field, str)
            field_name = field if isStr else field.get("name")
            if field_name in fields.keys():
                parents = self.get_parent_list(instance, field, field_name)
                fields[field_name] = (
                    parents[1 if isStr else field.get("index", 1)]
                    if len(parents) > (0 if isStr else field.get("index", 1))
                    else []
                )

        return fields

    def run_validation(self, data=...):
        if "added_by" in self.fields.keys():
            if not self.instance:
                data["added_by"] = self.request.user.id
            elif isinstance(self.instance, QuerySet):
                id = self.Meta.model._meta.pk.name
                instance = self.instance.filter(**{id: data.get(id, -1)}).first()
                if instance is None:
                    data["added_by"] = self.request.user.id
                else:
                    data["added_by"] = instance.added_by
        return super(serializers.ModelSerializer, self).run_validation(data)

    def get_filtered_data(self, fields):
        initial_fields = self.fields
        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        data = self.data
        self.fields = initial_fields
        return data

    def get_paginated_response(self, request: Request | None = None) -> dict:
        raise AssertionError(
            "This function is only callable when queryset is present and many=True is passed in the serializer"
        )

    def set_formatted_file_objects(self, instance, column_names: List[str], fields):
        for column_name in column_names:
            if column_name in fields.keys():
                fields[column_name] = (
                    {
                        "url": getattr(
                            getattr(getattr_recursive(instance, column_name), "file"),
                            "url",
                        ),
                        "id": getattr(getattr(instance, column_name), "id"),
                    }
                    if getattr(instance, column_name, None)
                    else None
                )
        return fields

    def run_before_pagination(self, instance):
        """Implement in child, to be run before pagination"""
        pass

    def run_after_pagination(self, instance):
        """Implement in child, to be run after pagination"""
        pass
