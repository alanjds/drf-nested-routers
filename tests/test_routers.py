"""
based upon https://github.com/alanjds/drf-nested-routers/issues/15
"""
from collections import namedtuple

from django.db import models
from django.test import TestCase
from rest_framework.viewsets import ModelViewSet
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter


QS = namedtuple('Queryset', ['model'])


class A(models.Model):
    name=models.CharField(max_length=255)
class B(models.Model):
    name=models.CharField(max_length=255)
    parent=models.ForeignKey(A)
class C(models.Model):
    name=models.CharField(max_length=255)
    parent=models.ForeignKey(B)

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
        self.assertEquals(urls[0].regex.pattern, u'^a/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<pk>[0-9a-f]{32})/$')

        self.assertEqual(self.a_router.parent_regex, u'a/(?P<a_pk>[0-9a-f]{32})/')
        urls = self.a_router.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(urls[0].regex.pattern, u'^a/(?P<a_pk>[0-9a-f]{32})/b/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<pk>[^/.]+)/$')

        self.assertEqual(self.b_router.parent_regex, u'a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/')
        urls = self.b_router.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(urls[0].regex.pattern, u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/c/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<a_pk>[0-9a-f]{32})/b/(?P<b_pk>[^/.]+)/c/(?P<pk>[^/.]+)/$')
