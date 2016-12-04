"""
Serializer fields that deal with relationships with nested resources.

These fields allow you to specify the style that should be used to represent
model relationships with hyperlinks.
"""
from __future__ import unicode_literals
from collections import Iterable
from functools import reduce  # import reduce from functools for compatibility with python 3
from django.core.exceptions import ImproperlyConfigured

import rest_framework.relations


# fix for basestring
try:
    basestring
except NameError:
    basestring = str


class NestedHyperlinkedRelatedField(rest_framework.relations.HyperlinkedRelatedField):
    lookup_field = 'pk'
    parent_lookup_field = 'parent'
    parent_lookup_related_field = 'pk'

    def __init__(self, *args, **kwargs):
        self.parent_lookup_field = kwargs.pop('parent_lookup_field', self.parent_lookup_field)
        self.parent_lookup_url_kwarg = kwargs.pop('parent_lookup_url_kwarg', self.parent_lookup_field)
        self.parent_lookup_related_field = kwargs.pop('parent_lookup_related_field', self.parent_lookup_related_field)
        super(NestedHyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        # check if lookup field exists
        if not hasattr(obj, self.lookup_field):
            raise ImproperlyConfigured(
                "Object %(obj)s does not have a field %(lookup_field)s" %
                {'obj': str(obj), 'lookup_field': self.lookup_field}
            )

        # get value of the primary lookup field
        lookup_value = getattr(obj, self.lookup_field)

        # set up kwargs with the initial lookup kwarg
        kwargs = {
            self.lookup_url_kwarg: lookup_value,
        }

        if isinstance(self.parent_lookup_url_kwarg, basestring):
            parent_lookup_object = getattr(obj, self.parent_lookup_field)
            parent_lookup_value = getattr(
                parent_lookup_object,
                self.parent_lookup_related_field
            ) if parent_lookup_object else None

            kwargs.update({self.parent_lookup_url_kwarg: parent_lookup_value})
        elif isinstance(self.parent_lookup_url_kwarg, Iterable):
            # iterate over all lookup fields, e.g. ("parent__pk", "pk")
            for underscored_lookup in self.parent_lookup_url_kwarg:
                # FIXME: handle errors

                # split each lookup by their __, e.g. "parent__pk" will be split into "parent" and "pk", or
                # "parent__super__pk" would be split itno "parent", "super" and "pk"
                lookups = underscored_lookup.split('__')

                # use the Django ORM to lookup this value, e.g., obj.parent.pk
                value = reduce(getattr, [obj] + lookups)

                # the lookup name needs to be created with single "_", and must only contain the last two entries of the
                # lookup field; "parent__super__pk" would be converted into "super_pk" and "parent__pk" into "parent_pk"
                lookup_name = "_".join(lookups[-2:])

                # store the lookup_name and value in kwargs, which is later passed to the reverse method
                kwargs.update({lookup_name: value})
            # end for
        # end if

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)

    def get_object(self, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and should return an
        object instance, or raise an `ObjectDoesNotExist` exception.
        """
        lookup_value = view_kwargs[self.lookup_url_kwarg]
        parent_lookup_value = view_kwargs[self.parent_lookup_url_kwarg]
        lookup_kwargs = {
            self.lookup_field: lookup_value,
            self.parent_lookup_field: parent_lookup_value,
        }
        return self.get_queryset().get(**lookup_kwargs)


class NestedHyperlinkedIdentityField(NestedHyperlinkedRelatedField):
    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        kwargs['read_only'] = True
        kwargs['source'] = '*'
        super(NestedHyperlinkedIdentityField, self).__init__(view_name=view_name, **kwargs)

    def use_pk_only_optimization(self):
        return False
