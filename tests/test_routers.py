"""
based upon https://github.com/alanjds/drf-nested-routers/issues/15
"""
from collections import namedtuple
from django.db import models
from django.test import TestCase
from rest_framework.viewsets import ModelViewSet
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter

from tests.helpers import get_regex_pattern


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
        self.assertEquals(len(urls), 2)
        self.assertEquals(get_regex_pattern(urls[0]), u'^a/$')
        self.assertEquals(get_regex_pattern(urls[1]), u'^a/(?P<pk>[0-9a-f]{32})/$')

        self.assertEqual(self.a_router.parent_regex, u'a/(?P<a_pk>[0-9a-f]{32})/')
        urls = self.a_router.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(get_regex_pattern(urls[0]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/$')
        self.assertEquals(get_regex_pattern(urls[1]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<pk>[^/.]+)/$')

        self.assertEqual(self.b_router.parent_regex, u'a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/')
        urls = self.b_router.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(get_regex_pattern(urls[0]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/c/$')
        self.assertEquals(get_regex_pattern(urls[1]), u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/c/(?P<pk>[^/.]+)/$')


class TestEmptyPrefix(TestCase):
    def setUp(self):
        self.router = SimpleRouter()
        self.router.register(r'', AViewSet)
        self.a_router = NestedSimpleRouter(self.router, r'', lookup='a')
        self.a_router.register(r'b', BViewSet)

    def test_empty_prefix(self):
        urls = self.router.urls
        urls = self.a_router.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(get_regex_pattern(urls[0]), u'^(?P<a_pk>[0-9a-f]{32})/b/$')
        self.assertEquals(get_regex_pattern(urls[1]), u'^(?P<a_pk>[0-9a-f]{32})/b/(?P<pk>[^/.]+)/$')


class TestBadLookupValue(TestCase):
    def setUp(self):
        self.router = SimpleRouter()
        self.router.register(r'parents', AViewSet, base_name='ui-parent_1')

    def test_bad_lookup(self):
        with self.assertRaises(ValueError):
            self.a_router = NestedSimpleRouter(self.router, r'parents', lookup='ui-parent_2')
            self.a_router.register(r'child', BViewSet, base_name='ui-parent-child')
