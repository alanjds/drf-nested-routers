class NestedViewSetMixin(object):
    def get_queryset(self):
        """
        Filter the `QuerySet` based on its parents as defined in the
        `serializer_class.parent_lookup_kwargs`.
        """
        queryset = super(NestedViewSetMixin, self).get_queryset()
        serializer_class = self.get_serializer_class()
        if hasattr(serializer_class, 'parent_lookup_kwargs') and hasattr(self, 'kwargs') and self.kwargs:
            orm_filters = {}
            for query_param, field_name in serializer_class.parent_lookup_kwargs.items():
                orm_filters[field_name] = self.kwargs[query_param]
            return queryset.filter(**orm_filters)
        return queryset
