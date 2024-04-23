from __future__ import annotations

from typing import Any, TypeVar

import rest_framework.serializers
from django.db.models import Model
from rest_framework.fields import Field
from rest_framework.utils.model_meta import RelationInfo
from rest_framework_nested.relations import NestedHyperlinkedIdentityField, NestedHyperlinkedRelatedField
try:
    from rest_framework.utils.field_mapping import get_nested_relation_kwargs
except ImportError:
    pass
    # passing because NestedHyperlinkedModelSerializer can't be used anyway
    #    if version too old.


T_Model = TypeVar('T_Model', bound=Model)


class NestedHyperlinkedModelSerializer(rest_framework.serializers.HyperlinkedModelSerializer[T_Model]):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships with compound keys instead
    of primary key relationships.  Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.

    NOTE: this only works with DRF 3.1.0 and above.
    """
    parent_lookup_kwargs = {
        'parent_pk': 'parent__pk'
    }

    serializer_url_field = NestedHyperlinkedIdentityField
    serializer_related_field = NestedHyperlinkedRelatedField

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.parent_lookup_kwargs = kwargs.pop('parent_lookup_kwargs', self.parent_lookup_kwargs)
        super().__init__(*args, **kwargs)

    def build_url_field(self, field_name: str, model_class: T_Model) -> tuple[type[Field], dict[str, Any]]:
        field_class, field_kwargs = super().build_url_field(
            field_name,
            model_class
        )
        field_kwargs['parent_lookup_kwargs'] = self.parent_lookup_kwargs

        return field_class, field_kwargs

    def build_nested_field(
        self, field_name: str, relation_info: RelationInfo, nested_depth: int
    ) -> tuple[type[Field], dict[str, Any]]:
        """
        Create nested fields for forward and reverse relationships.
        """
        class NestedSerializer(NestedHyperlinkedModelSerializer):
            class Meta:
                model = relation_info.related_model
                depth = nested_depth - 1
                fields = '__all__'

        field_class = NestedSerializer
        field_kwargs = get_nested_relation_kwargs(relation_info)

        return field_class, field_kwargs
