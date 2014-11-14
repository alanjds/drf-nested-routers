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


class NestedSimpleRouter(rest_framework.routers.SimpleRouter):
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

        nested_routes = []
        parent_lookup_regex = parent_router.get_lookup_regex(parent_viewset, self.nest_prefix)
        self.parent_regex = '{parent_prefix}/{parent_lookup_regex}/'.format(parent_prefix=parent_prefix, parent_lookup_regex=parent_lookup_regex)

        # escape braces in parent_regex
        # e.g., if it has lookup_value_regex = '[0-9a-f]{32}'
        self.parent_regex = self.parent_regex.replace('{', '{{').replace('}', '}}')

        if hasattr(parent_router, 'parent_regex'):
            self.parent_regex = parent_router.parent_regex+self.parent_regex

        for route in self.routes:
            route_contents = route._asdict()

            route_contents['url'] = route.url.replace('^', '^'+self.parent_regex)
            nested_routes.append(type(route)(**route_contents))

        self.routes = nested_routes
