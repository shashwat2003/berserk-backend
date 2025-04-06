from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(OpenApiTypes.ANY)
class NullField(serializers.Field):

    def to_internal_value(self, data):
        if data is None:
            return None
        return super().to_internal_value(data)

    def to_representation(self, value):
        if value is None:
            return None
        return super().to_representation(value)
