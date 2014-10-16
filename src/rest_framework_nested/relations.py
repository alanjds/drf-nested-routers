"""
Serializer fields that deal with relationships with nested resources.

These fields allow you to specify the style that should be used to represent
model relationships with hyperlinks.
"""
from __future__ import unicode_literals

import warnings

import rest_framework.relations
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import resolve, get_script_prefix, NoReverseMatch
from django.utils.translation import ugettext_lazy as _
from rest_framework.compat import urlparse
from rest_framework.fields import Field
from rest_framework.reverse import reverse


class HyperlinkedRelatedField(rest_framework.relations.RelatedField):
    """
    Represents a relationship using hyperlinking.
    """
    read_only = False
    lookup_field = 'pk'
    domain_lookup_field = 'domain__pk'

    default_error_messages = {
        'no_match': _('Invalid hyperlink - No URL match'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match'),
        'configuration_error': _(
            'Invalid hyperlink due to configuration error'
        ),
        'does_not_exist': _("Invalid hyperlink - object does not exist."),
        'incorrect_type': _(
            'Incorrect type.  Expected url string, received %s.'
        ),
    }

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            raise ValueError("Hyperlinked field requires 'view_name' kwarg")

        self.lookup_field = kwargs.pop('lookup_field', self.lookup_field)
        self.format = kwargs.pop('format', None)

        super(HyperlinkedRelatedField, self).__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        lookup_field = getattr(obj, self.lookup_field)
        domain_lookup_field = getattr(obj, self.domain_lookup_field)
        # TODO find out domain_lookup_field
        kwargs = {self.lookup_field: lookup_field,
                  self.domain_lokup_field: domain_lookup_field}
        return reverse(
            view_name,
            kwargs=kwargs,
            request=request,
            format=format
        )

        raise NoReverseMatch()

    def get_object(self, queryset, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and the queryset, and should
        return an object instance, or raise an `ObjectDoesNotExist` exception.
        """
        lookup = view_kwargs.get(self.lookup_field, None)
        pk = view_kwargs.get(self.pk_url_kwarg, None)
        slug = view_kwargs.get(self.slug_url_kwarg, None)

        if lookup is not None:
            filter_kwargs = {self.lookup_field: lookup}
        elif pk is not None:
            filter_kwargs = {'pk': pk}
        elif slug is not None:
            filter_kwargs = {self.slug_field: slug}
        else:
            raise ObjectDoesNotExist()

        return queryset.get(**filter_kwargs)

    def to_native(self, obj):
        view_name = self.view_name
        request = self.context.get('request', None)
        format = self.format or self.context.get('format', None)

        if request is None:
            msg = (
                "Using `HyperlinkedRelatedField` without including the request"
                " in the serializer context is deprecated. "
                "Add `context={'request': request}` when instantiating "
                "the serializer."
            )
            warnings.warn(msg, DeprecationWarning, stacklevel=4)

        # If the object has not yet been saved then we cannot hyperlink to it.
        if getattr(obj, 'pk', None) is None:
            return

        # Return the hyperlink, or error if incorrectly configured.
        try:
            return self.get_url(obj, view_name, request, format)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise Exception(msg % view_name)

    def from_native(self, value):
        # Convert URL -> model instance pk
        # TODO: Use values_list
        queryset = self.queryset
        if queryset is None:
            raise Exception(
                'Writable related fields must include a `queryset` argument'
            )

        try:
            http_prefix = value.startswith(('http:', 'https:'))
        except AttributeError:
            msg = self.error_messages['incorrect_type']
            raise ValidationError(msg % type(value).__name__)

        if http_prefix:
            # If needed convert absolute URLs to relative path
            value = urlparse.urlparse(value).path
            prefix = get_script_prefix()
            if value.startswith(prefix):
                value = '/' + value[len(prefix):]

        try:
            match = resolve(value)
        except Exception:
            raise ValidationError(self.error_messages['no_match'])

        if match.view_name != self.view_name:
            raise ValidationError(self.error_messages['incorrect_match'])

        try:
            return self.get_object(queryset, match.view_name,
                                   match.args, match.kwargs)
        except (ObjectDoesNotExist, TypeError, ValueError):
            raise ValidationError(self.error_messages['does_not_exist'])


class HyperlinkedIdentityField(Field):
    """
    Represents the instance, or a property on the instance, using hyperlinking.
    """
    lookup_field = 'pk'
    read_only = True

    # These are all pending deprecation

    slug_field = 'slug'
    slug_url_kwarg = None  # Defaults to same as `slug_field` unless overridden

    def __init__(self, *args, **kwargs):
        try:
            self.view_name = kwargs.pop('view_name')
        except KeyError:
            msg = "HyperlinkedIdentityField requires 'view_name' argument"
            raise ValueError(msg)

        self.format = kwargs.pop('format', None)
        lookup_field = kwargs.pop('lookup_field', None)
        self.lookup_field = lookup_field or self.lookup_field

        # These are pending deprecation
        if 'pk_url_kwarg' in kwargs:
            msg = (
                'pk_url_kwarg is pending deprecation. '
                'Use lookup_field instead.'
            )
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_url_kwarg' in kwargs:
            msg = (
                'slug_url_kwarg is pending deprecation. '
                'Use lookup_field instead.'
            )
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)
        if 'slug_field' in kwargs:
            msg = (
                'slug_field is pending deprecation. Use lookup_field instead.'
            )
            warnings.warn(msg, PendingDeprecationWarning, stacklevel=2)

        self.slug_field = kwargs.pop('slug_field', self.slug_field)
        default_slug_kwarg = self.slug_url_kwarg or self.slug_field
        self.pk_url_kwarg = kwargs.pop('pk_url_kwarg', self.pk_url_kwarg)
        self.slug_url_kwarg = kwargs.pop('slug_url_kwarg', default_slug_kwarg)

        super(HyperlinkedIdentityField, self).__init__(*args, **kwargs)

    def field_to_native(self, obj, field_name):
        request = self.context.get('request', None)
        format = self.context.get('format', None)
        view_name = self.view_name

        if request is None:
            warnings.warn(
                "Using `HyperlinkedIdentityField` without including the "
                "request in the serializer context is deprecated. "
                "Add `context={'request': request}` when instantiating "
                "the serializer.",
                DeprecationWarning,
                stacklevel=4
            )

        # By default use whatever format is given for the current context
        # unless the target is a different type to the source.
        #
        # Eg. Consider a HyperlinkedIdentityField pointing from a json
        # representation to an html property of that representation...
        #
        # '/snippets/1/' should link to '/snippets/1/highlight/'
        # ...but...
        # '/snippets/1/.json' should link to '/snippets/1/highlight/.html'
        if format and self.format and self.format != format:
            format = self.format

        # Return the hyperlink, or error if incorrectly configured.
        try:
            return self.get_url(obj, view_name, request, format)
        except NoReverseMatch:
            msg = (
                'Could not resolve URL for hyperlinked relationship using '
                'view name "%s". You may have failed to include the related '
                'model in your API, or incorrectly configured the '
                '`lookup_field` attribute on this field.'
            )
            raise Exception(msg % view_name)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        lookup_field = getattr(obj, self.lookup_field, None)
        kwargs = {self.lookup_field: lookup_field}

        # Handle unsaved object case
        if lookup_field is None:
            return None

        try:
            return reverse(
                view_name,
                kwargs=kwargs,
                request=request,
                format=format
            )
        except NoReverseMatch:
            pass

        if self.pk_url_kwarg != 'pk':
            # Only try pk lookup if it has been explicitly set.
            # Otherwise, the default `lookup_field = 'pk'` has us covered.
            kwargs = {self.pk_url_kwarg: obj.pk}
            try:
                return reverse(
                    view_name,
                    kwargs=kwargs,
                    request=request,
                    format=format
                )
            except NoReverseMatch:
                pass

        slug = getattr(obj, self.slug_field, None)
        if slug:
            # Only use slug lookup if a slug field exists on the model
            kwargs = {self.slug_url_kwarg: slug}
            try:
                return reverse(
                    view_name,
                    kwargs=kwargs,
                    request=request,
                    format=format
                )
            except NoReverseMatch:
                pass

        raise NoReverseMatch()
