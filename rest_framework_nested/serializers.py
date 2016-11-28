import rest_framework.serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework_nested.relations import NestedHyperlinkedIdentityField
from collections import Iterable

try:
    from rest_framework.utils.field_mapping import get_nested_relation_kwargs
except ImportError:
    pass # passing because NestedHyperlinkedModelSerializer can't be used anyway
         #    if version too old.


class NestedHyperlinkedModelSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
    """
    A type of `ModelSerializer` that uses hyperlinked relationships with compound keys instead
    of primary key relationships.  Specifically:

    * A 'url' field is included instead of the 'id' field.
    * Relationships to other instances are hyperlinks, instead of primary keys.

    NOTE: this only works with DRF 3.1.0 and above.
    """
    parent_lookup_field = 'parent'
    parent_lookup_related_field = 'pk'
    parent_lookup_url_kwarg = 'parent_pk'

    serializer_url_field = NestedHyperlinkedIdentityField

    def __init__(self, *args, **kwargs):
        self.parent_lookup_field = kwargs.pop('parent_lookup_field', self.parent_lookup_field)
        self.parent_lookup_related_field = kwargs.pop('parent_lookup_related_field', self.parent_lookup_related_field)
        self.parent_lookup_url_kwarg = kwargs.pop('parent_lookup_url_kwarg', self.parent_lookup_url_kwarg)

        return super(NestedHyperlinkedModelSerializer, self).__init__(*args, **kwargs)

    def build_url_field(self, field_name, model_class):
        field_class, field_kwargs = super(NestedHyperlinkedModelSerializer, self).build_url_field(field_name, model_class)
        field_kwargs['parent_lookup_field'] = self.parent_lookup_field
        field_kwargs['parent_lookup_related_field'] = self.parent_lookup_related_field
        field_kwargs['parent_lookup_url_kwarg'] = self.parent_lookup_url_kwarg

        return field_class, field_kwargs

    def build_nested_field(self, field_name, relation_info, nested_depth):
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


class NestedHyperlinkedIdentityField(HyperlinkedIdentityField):
    """HyperlinkedIdentifyField for nested relations."""

    lookup_fields = ()

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop('lookup_fields', None)
        super(NestedHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        if not isinstance(self.lookup_fields, Iterable):
            # FIXME: raise improperly configured error
            pass

        kwargs = {}
        for underscored_lookup in self.lookup_fields:
            # FIXME: handle errors
            lookups = underscored_lookup.split('__')
            from functools import reduce  # Python 3 Fix for reduce
            value = reduce(getattr, [obj]+lookups)
            lookup_name = "_".join(lookups[-2:])
            kwargs.update({lookup_name: value})

        return self.reverse(
            view_name,
            kwargs=kwargs,
            request=request,
            format=format
        )