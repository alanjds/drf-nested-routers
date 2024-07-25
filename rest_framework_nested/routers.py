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
        path('', include(router.urls)),
        path('', include(domains_router.urls)),
    )

    router = routers.DefaultRouter()
    router.register('users', UserViewSet, 'user')
    router.register('accounts', AccountViewSet, 'account')

    urlpatterns = router.urls
"""

from __future__ import annotations

import sys
import re
from typing import Any

from rest_framework.routers import DefaultRouter, SimpleRouter

if sys.version_info[0] < 3:
    IDENTIFIER_REGEX = re.compile(r"^[^\d\W]\w*$")
else:
    IDENTIFIER_REGEX = re.compile(r"^[^\d\W]\w*$", re.UNICODE)


class LookupMixin:
    """
    Deprecated.

    No method override is needed since Django Rest Framework 2.4.
    """


class NestedMixin:
    def __init__(
        self,
        parent_router: SimpleRouter | DefaultRouter | NestedMixin,
        parent_prefix: str,
        *args: Any,
        **kwargs: Any
    ) -> None:
        self.parent_router = parent_router
        self.parent_prefix = parent_prefix
        self.nest_count = getattr(parent_router, 'nest_count', 0) + 1
        self.nest_prefix = kwargs.pop('lookup', f'nested_{self.nest_count}') + '_'
        self.use_regex_path = kwargs.get('use_regex_path', True)

        super().__init__(*args, **kwargs)

        if 'trailing_slash' not in kwargs:
            # Inherit trailing_slash only when not specified explicitly.
            #
            # drf transposes the trailing_slash argument into the actual appended value
            # within the route urls. This means that, on the parent class, trailing_slash
            # is either '/' or '' for the expected kwarg values True or False, respectively.
            # If, however, the trailing_slash property has been further customized beyond
            # those two values (for example, to add an optional slash with '/?'), we won't
            # be able to set it through the kwargs.
            #
            # By copying the value of trailing_slash directly, we ensure that our inherited
            # behavior is ALWAYS consistent with the parent. If we didn't, we might create
            # a situation where the parent's trailing slash is truthy (but not '/') and
            # we set our trailing slash to just '/', leading to inconsistent behavior.
            self.trailing_slash = parent_router.trailing_slash  # type: ignore[has-type]

        parent_registry = [
            registered for registered
            in self.parent_router.registry  # type: ignore[union-attr]
            if registered[0] == self.parent_prefix
        ]
        try:
            parent_registry_item = parent_registry[0]
            parent_prefix, parent_viewset, parent_basename = parent_registry_item
        except:
            raise RuntimeError('parent registered resource not found')

        self.check_valid_name(self.nest_prefix)

        nested_routes = []
        parent_lookup_regex = parent_router.get_lookup_regex(parent_viewset, self.nest_prefix)  # type: ignore[union-attr]

        self.parent_regex = f'{parent_prefix}/{parent_lookup_regex}/'
        # If there is no parent prefix, the first part of the url is probably
        #   controlled by the project's urls.py and the router is in an app,
        #   so a slash in the beginning will (A) cause Django to give warnings
        #   and (B) generate URLs that will require using `//`
        if not self.parent_prefix and self.parent_regex[0] == '/':
            self.parent_regex = self.parent_regex[1:]
        if hasattr(parent_router, 'parent_regex'):
            self.parent_regex = parent_router.parent_regex + self.parent_regex

        for route in self.routes:  # type: ignore[has-type]
            route_contents = route._asdict()

            # This will get passed through .format in a little bit, so we need
            # to escape it
            escaped_parent_regex = self.parent_regex.replace('{', '{{').replace('}', '}}')

            if self.use_regex_path:
                route_contents['url'] = route.url.replace('^', '^' + escaped_parent_regex)
            else:
                route_contents['url'] = escaped_parent_regex + route_contents['url']

            nested_routes.append(type(route)(**route_contents))

        self.routes = nested_routes

    def check_valid_name(self, value: str) -> None:
        if IDENTIFIER_REGEX.match(value) is None:
            raise ValueError(f"lookup argument '{value}' needs to be valid python identifier")


class NestedSimpleRouter(NestedMixin, SimpleRouter):  # type: ignore[misc]
    """ Create a NestedSimpleRouter nested within `parent_router`
    Args:

    parent_router: Parent router. Maybe be a SimpleRouter or another nested
        router.

    parent_prefix: The url prefix within parent_router under which the
        routes from this router should be nested.

    lookup:
        The regex variable that matches an instance of the parent-resource
        will be called '<lookup>_<parent-viewset.lookup_field>'
        In the example above, lookup=domain and the parent viewset looks up
        on 'pk' so the parent lookup regex will be 'domain_pk'.
        Default: 'nested_<n>' where <n> is 1+parent_router.nest_count

    """
    pass


class NestedDefaultRouter(NestedMixin, DefaultRouter):  # type: ignore[misc]
    """ Create a NestedDefaultRouter nested within `parent_router`
    Args:

    parent_router: Parent router. Maybe be a DefaultRouter or another nested
        router.

    parent_prefix: The url prefix within parent_router under which the
        routes from this router should be nested.

    lookup:
        The regex variable that matches an instance of the parent-resource
        will be called '<lookup>_<parent-viewset.lookup_field>'
        In the example above, lookup=domain and the parent viewset looks up
        on 'pk' so the parent lookup regex will be 'domain_pk'.
        Default: 'nested_<n>' where <n> is 1+parent_router.nest_count

    """
    pass
