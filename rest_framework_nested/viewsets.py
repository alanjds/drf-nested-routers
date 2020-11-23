from django.core.exceptions import ImproperlyConfigured


class NestedViewSetMixin(object):
    def get_queryset(self):
        """
        Filter the `QuerySet` based on its parents as defined in the
        `serializer_class.parent_lookup_kwargs` or `viewset.parent_lookup_kwargs`
        """
        queryset = super(NestedViewSetMixin, self).get_queryset()

        parent_lookup_kwargs = getattr(self, 'parent_lookup_kwargs', None)

        if not parent_lookup_kwargs:
            serializer_class = self.get_serializer_class()
            parent_lookup_kwargs = getattr(serializer_class, 'parent_lookup_kwargs', None)

        if parent_lookup_kwargs:
            orm_filters = {}
            for query_param, field_name in parent_lookup_kwargs.items():
                orm_filters[field_name] = self.kwargs[query_param]
            return queryset.filter(**orm_filters)

        raise ImproperlyConfigured("Views with NestedViewSetMixin must have 'parent_lookup_kwargs' defined")
