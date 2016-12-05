from django.core.exceptions import ImproperlyConfigured
import rest_framework.serializers
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework_nested.relations import NestedHyperlinkedIdentityField
from collections import Iterable
from functools import reduce  # import reduce from functools for compatibility with python 3

try:
    from rest_framework.utils.field_mapping import get_nested_relation_kwargs
except ImportError:
    pass  # passing because NestedHyperlinkedModelSerializer can't be used anyway if version too old.


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
    """
    HyperlinkedIdentifyField for nested relations.

    This field provides the ability to get the URLs of nested viewsets. While the normal DRF url serializers are only
    to lookup a single primary key (e.g., "pk") for the URLs, this serializer class is able to follow the path of the
    Django ORM, e.g., foreignkey1__pk.

    This allows us to link to views that are built like this: "/parent/{parent__pk}/child/{pk}"
    where one parent has multiple children, but a child is linked to a single parent.

    This serializer field also supports multiple nested viewsets in each other, e.g. Super -> Parent -> Child:
    "/super/{parent__super__pk}/parent/{parent__pk}/child/{pk}"

    Parameters:
        lookup_fields: A list of fields that are used to lookup a primary key value; fields can be written in django
                        db lookup syntax, e.g. ("parent__pk", "pk") or ("parent__super__pk", "parent__pk", "pk")
        view_name: Name of the (REST API) view that should be used to create the hyperlink, e.g., child_detail
    """

    lookup_fields = ()

    def __init__(self, *args, **kwargs):
        self.lookup_fields = kwargs.pop('lookup_fields', None)
        # let the parent class handle the remaining attributes such as view_name
        super(NestedHyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk is None:
            return None

        # check whether the lookup_fields parameter provided in kwargs (see __init__) is iterable (e.g. a list)
        if not isinstance(self.lookup_fields, Iterable):
            raise ImproperlyConfigured(
                "In NestedHyperlinkedIdentityField: lookup_fields must be iterable, not %(lookup_fields)s" %
                {'lookup_fields': str(self.lookup_fields)}
            )

        kwargs = {}

        # iterate over all lookup fields, e.g. ("parent__pk", "pk")
        for underscored_lookup in self.lookup_fields:
            # FIXME: handle errors

            # split each lookup by their __, e.g. "parent__pk" will be split into "parent" and "pk", or
            # "parent__super__pk" would be split itno "parent", "super" and "pk"
            lookups = underscored_lookup.split('__')

            # use the Django ORM to lookup this value
            value = reduce(getattr, [obj] + lookups)

            # the lookup name needs to be created with single "_", and must only contain the last two entries of the
            # lookup field; "parent__super__pk" would be converted into "super_pk" and "parent__pk" into "parent_pk"
            lookup_name = "_".join(lookups[-2:])

            # store the lookup_name and value in kwargs, which is later passed to the reverse method
            kwargs.update({lookup_name: value})

        return self.reverse(
            view_name,
            kwargs=kwargs,
            request=request,
            format=format
        )
