"""
based upon https://github.com/alanjds/drf-nested-routers/issues/15
"""
from collections import namedtuple
from django.db import models
from django.test import TestCase
from rest_framework.viewsets import ModelViewSet
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter

from tests.helpers import get_regex_pattern


def pattern_from_url(url_pattern):
    """
    Finds the internal stringified pattern for a URL across
    Django versions.

    Newer versions of Django use URLPattern, as opposed to
    RegexURLPattern.
    """
    if hasattr(url_pattern, 'pattern'):
        pattern = str(url_pattern.pattern)
    elif hasattr(url_pattern._regex, 'pattern'):
        pattern = str(url_pattern.regex.pattern)
    else:
        pattern = url_pattern._regex

    return pattern


QS = namedtuple('Queryset', ['model'])


class A(models.Model):
    name = models.CharField(max_length=255)


class B(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(A, on_delete=models.CASCADE)


class C(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(B, on_delete=models.CASCADE)


class AViewSet(ModelViewSet):
    lookup_value_regex = '[0-9a-f]{32}'
    model = A
    queryset = QS(A)


class BViewSet(ModelViewSet):
    model = B
    queryset = QS(B)


class CViewSet(ModelViewSet):
    model = C
    queryset = QS(C)


class TestNestedSimpleRouter(TestCase):
    def setUp(self):
        self.router = SimpleRouter()
        self.router.register(r'a', AViewSet)
        self.a_router = NestedSimpleRouter(self.router, r'a', lookup='a')
        self.a_router.register(r'b', BViewSet)
        self.b_router = NestedSimpleRouter(self.a_router, r'b', lookup='b')
        self.b_router.register(r'c', CViewSet)

    def test_recursive_nested_simple_routers(self):
        self.assertFalse(hasattr(self.router, 'parent_regex'))
        urls = self.router.urls
        self.assertEqual(len(urls), 2)
        self.assertEqual(get_regex_pattern(urls[0]), u'^a/$')
        self.assertEqual(get_regex_pattern(urls[1]), u'^a/(?P<pk>[0-9a-f]{32})/$')

        self.assertEqual(self.a_router.parent_regex, u'a/(?P<a_pk>[0-9a-f]{32})/')
        urls = self.a_router.urls
        self.assertEqual(len(urls), 2)
        self.assertEqual(get_regex_pattern(urls[0]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/$')
        self.assertEqual(get_regex_pattern(urls[1]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<pk>[^/.]+)/$')

        self.assertEqual(self.b_router.parent_regex, u'a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/')
        urls = self.b_router.urls
        self.assertEqual(len(urls), 2)
        self.assertEqual(get_regex_pattern(urls[0]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/c/$')
        self.assertEqual(get_regex_pattern(urls[1]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/c/(?P<pk>[^/.]+)/$')


class TestEmptyPrefix(TestCase):
    def setUp(self):
        self.router = SimpleRouter()
        self.router.register(r'', AViewSet)
        self.a_router = NestedSimpleRouter(self.router, r'', lookup='a')
        self.a_router.register(r'b', BViewSet)

    def test_empty_prefix(self):
        urls = self.router.urls
        urls = self.a_router.urls
        self.assertEqual(len(urls), 2)
        self.assertEqual(get_regex_pattern(urls[0]), u'^(?P<a_pk>[0-9a-f]{32})/b/$')
        self.assertEqual(get_regex_pattern(urls[1]), u'^(?P<a_pk>[0-9a-f]{32})/b/(?P<pk>[^/.]+)/$')


class TestBadLookupValue(TestCase):
    def setUp(self):
        self.router = SimpleRouter()
        self.router.register(r'parents', AViewSet, basename='ui-parent_1')

    def test_bad_lookup(self):
        with self.assertRaises(ValueError):
            self.a_router = NestedSimpleRouter(self.router, r'parents', lookup='ui-parent_2')
            self.a_router.register(r'child', BViewSet, basename='ui-parent-child')


class TestRouterSettingInheritance(TestCase):
    """
    Ensure that nested routers inherit the trailing_slash option from
    their parent unless explicitly told not to.

    note: drf transforms the boolean from the kwargs into an internal
    pattern string, so it required to test these values instead of
    the boolean.

        trailing_slash=True -> '/'
        trailing_slash=False -> ''

    trailing_slash should
        - always give priority to the value explicitly defined on the router
        - if inherited, use the trailing slash exactly as set in the parent
    """

    def _assertHasTrailingSlash(self, router):
        self.assertEqual(router.trailing_slash, u'/', "router does not have trailing slash when it should")
        self.assertTrue(pattern_from_url(router.urls[0]).endswith('/$'),
                        "router created url without trailing slash when it should have")

    def _assertDoesNotHaveTrailingSlash(self, router):
        self.assertEqual(router.trailing_slash, u'', "router has trailing slash when it should not")
        self.assertFalse(pattern_from_url(router.urls[0]).endswith('/$'),
                         "router created url with trailing slash when it should not have")

    def test_inherits_no_trailing_slash(self):
        """
        Test whether the trailing_slash=False value is inherited when it
        is unspecified on the nested router.
        """
        router = SimpleRouter(trailing_slash=False)
        router.register('a', AViewSet)
        a_router = NestedSimpleRouter(router, 'a', lookup='a')
        a_router.register('b', BViewSet)

        self._assertDoesNotHaveTrailingSlash(a_router)

    def test_inherits_trailing_slash(self):
        """
        Test whether the trailing_slash=False value is inherited when it
        is unspecified on the nested router.
        """
        router = SimpleRouter(trailing_slash=True)
        router.register('a', AViewSet)
        a_router = NestedSimpleRouter(router, 'a', lookup='a')
        a_router.register('b', BViewSet)

        self._assertHasTrailingSlash(a_router)

    def test_explicit_no_trailing_slash(self):
        router = SimpleRouter(trailing_slash=True)
        router.register('a', AViewSet)
        a_router = NestedSimpleRouter(router, 'a', lookup='a', trailing_slash=False)
        a_router.register('b', BViewSet)

        self._assertDoesNotHaveTrailingSlash(a_router)

    def test_explicit_trailing_slash(self):
        """
        Test whether the trailing_slash=False value is properly overridden when setting
        trailing_slash=True on the nested router.
        """
        router = SimpleRouter(trailing_slash=False)
        router.register('a', AViewSet)
        a_router = NestedSimpleRouter(router, 'a', lookup='a', trailing_slash=True)
        a_router.register('b', BViewSet)

        self._assertHasTrailingSlash(a_router)

    def test_inherits_nonstandard_trailing_slash(self):
        """
        Test whether the trailing_slash attribute, when set with a custom value,
        is inherited by the nested routed.
        """
        router = SimpleRouter()
        router.trailing_slash = '/?'
        router.register('a', AViewSet)
        a_router = NestedSimpleRouter(router, 'a', lookup='a')
        a_router.register('b', BViewSet)

        self.assertEqual(a_router.trailing_slash, u'/?', "router does not have trailing slash when it should")
        self.assertTrue(pattern_from_url(a_router.urls[0]).endswith('/?$'),
                        "router created url without trailing slash when it should have")
