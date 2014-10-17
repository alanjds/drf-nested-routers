"""
Routers for nested resources.

Example:

    # urls.py

    from rest_framework_nested import routers

    router = routers.SimpleRouter()
    router.register(r'domains', DomainViewSet)

    domains_router = routers.NestedSimpleRouter(router, r'domains', lookup='domain')
    domains_router.register(r'nameservers', NameserverViewSet)

    url_patterns = patterns('',
        url(r'^', include(router.urls)),
            url(r'^', include(domains_router.urls)),
            )

        router = routers.DefaultRouter()
        router.register('users', UserViewSet, 'user')
        router.register('accounts', AccountViewSet, 'account')

        urlpatterns = router.urls
"""

from __future__ import unicode_literals

import rest_framework.routers


class SimpleRouter(rest_framework.routers.SimpleRouter):
    """ Improvement of rest_framework.routers.SimpleRouter that allows the
    lookup of urls of nested resources.

    """
    def get_lookup_regex(self, viewset, lookup_prefix=''):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.
        """
        base_regex = '(?P<{lookup_prefix}{lookup_field}>[^/]+)'
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        return base_regex.format(lookup_field=lookup_field, lookup_prefix=lookup_prefix)

class NestedSimpleRouter(SimpleRouter):
    def __init__(self, parent_router, parent_prefix, *args, **kwargs):
        self.parent_router = parent_router
        self.parent_prefix = parent_prefix
        self.nest_count = getattr(parent_router, 'nest_count', 0) +1
        self.nest_prefix = kwargs.pop('lookup', 'nested_%i' % self.nest_count) + '_'
        super(NestedSimpleRouter, self).__init__(*args, **kwargs)

        parent_registry = [registered for registered in self.parent_router.registry if registered[0] == self.parent_prefix]
        try:
            parent_registry = parent_registry[0]
            parent_prefix, parent_viewset, parent_basename = parent_registry
        except:
            raise RuntimeError('parent registered resource not found')

        parent_lookup_regex = parent_router.get_lookup_regex(parent_viewset, self.nest_prefix)
        self.parent_regex = '{parent_prefix}/{parent_lookup_regex}/'.format(parent_prefix=parent_prefix, parent_lookup_regex=parent_lookup_regex)
        if hasattr(parent_router, 'parent_regex'):
            self.parent_regex = parent_router.parent_regex+self.parent_regex

        nested_routes = []
        for route in self.routes:
            nested_routes.append(route._replace(url=route.url.replace('^', '^'+self.parent_regex)))

        self.routes = nested_routes
