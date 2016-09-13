import rest_framework.serializers
from rest_framework_nested.relations import NestedHyperlinkedIdentityField
from rest_framework.utils.field_mapping import get_nested_relation_kwargs


class NestedHyperlinkedModelSerializer(rest_framework.serializers.HyperlinkedModelSerializer):
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
