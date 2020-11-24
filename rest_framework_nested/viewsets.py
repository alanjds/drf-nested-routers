from django.core.exceptions import ImproperlyConfigured


class NestedViewSetMixin(object):
    def _get_parent_lookup_kwargs(self) -> dict:
        """
        Locates and returns the `parent_lookup_kwargs` dict informing
        how the kwargs in the URL maps to the parents of the model instance

        For now, fetches from `parent_lookup_kwargs`
        on the ViewSet or Serializer attached. This may change on the future.
        """
        parent_lookup_kwargs = getattr(self, 'parent_lookup_kwargs', None)

        if not parent_lookup_kwargs:
            serializer_class = self.get_serializer_class()
            parent_lookup_kwargs = getattr(serializer_class, 'parent_lookup_kwargs', None)

        if not parent_lookup_kwargs:
            raise ImproperlyConfigured(
                "NestedViewSetMixin need 'parent_lookup_kwargs' to find the parent from the URL"
            )

        return parent_lookup_kwargs

    def get_queryset(self):
        """
        Filter the `QuerySet` based on its parents as defined in the
        `serializer_class.parent_lookup_kwargs` or `viewset.parent_lookup_kwargs`
        """
        queryset = super(NestedViewSetMixin, self).get_queryset()

        orm_filters = {}
        parent_lookup_kwargs = self._get_parent_lookup_kwargs()
        for query_param, field_name in parent_lookup_kwargs.items():
            orm_filters[field_name] = self.kwargs[query_param]
        return queryset.filter(**orm_filters)
