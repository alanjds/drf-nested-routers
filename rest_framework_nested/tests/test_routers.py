"""
based upon https://github.com/alanjds/drf-nested-routers/issues/15
"""
from django.db import models
from django.test import TestCase
from rest_framework.viewsets import ModelViewSet
from rest_framework.routers import SimpleRouter
from rest_framework_nested.routers import NestedSimpleRouter

class A(models.Model):
    name=models.CharField(max_length=255)
class B(models.Model):
    name=models.CharField(max_length=255)
    parent=models.ForeignKey(A)
class C(models.Model):
    name=models.CharField(max_length=255)
    parent=models.ForeignKey(B)

class AViewSet(ModelViewSet):
    model = A

class BViewSet(ModelViewSet):
    model = B

class CViewSet(ModelViewSet):
    model = C


class AViewSetWithRegex(ModelViewSet):
    model = A
    lookup_value_regex = '[\d]{1,11}'

class BViewSetWithRegex(ModelViewSet):
    model = B
    lookup_value_regex = '[\d]{1,11}'

class CViewSetWithRegex(ModelViewSet):
    model = C
    lookup_value_regex = '[\d]{1,11}'


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
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<pk>[^/.]+)/$')

        self.assertEqual(self.a_router.parent_regex, u'a/(?P<a_pk>[^/.]+)/')
        urls = self.a_router.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(urls[0].regex.pattern, u'^a/(?P<a_pk>[^/.]+)/b/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<a_pk>[^/.]+)/b/(?P<pk>[^/.]+)/$')

        self.assertEqual(self.b_router.parent_regex, u'a/(?P<a_pk>[^/.]+)/b/(?P<b_pk>[^/.]+)/')
        urls = self.b_router.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(urls[0].regex.pattern, u'^a/(?P<a_pk>[^/.]+)/b/(?P<b_pk>[^/.]+)/c/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<a_pk>[^/.]+)/b/(?P<b_pk>[^/.]+)/c/(?P<pk>[^/.]+)/$')

class TestNestedSimpleRouterWithRegex(TestCase):
    def setUp(self):
        self.router_regex = SimpleRouter()
        self.router_regex.register(r'a', AViewSetWithRegex)
        self.a_router_regex = NestedSimpleRouter(self.router_regex, r'a', lookup='a')
        self.a_router_regex.register(r'b', BViewSetWithRegex)
        self.b_router_regex = NestedSimpleRouter(self.a_router_regex, r'b', lookup='b')
        self.b_router_regex.register(r'c', CViewSetWithRegex)

    def test_recursive_nested_simple_routers_with_custom_lookup_regex(self):
        self.assertFalse(hasattr(self.router_regex, 'parent_regex'))
        urls = self.router_regex.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(urls[0].regex.pattern, u'^a/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<pk>[\d]{1,11})/$')

        self.assertEqual(self.a_router_regex.parent_regex, u'a/(?P<a_pk>[\d]{{1,11}})/')
        urls = self.a_router_regex.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(urls[0].regex.pattern, u'^a/(?P<a_pk>[\d]{1,11})/b/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<a_pk>[\d]{1,11})/b/(?P<pk>[\d]{1,11})/$')

        self.assertEqual(self.b_router_regex.parent_regex, u'a/(?P<a_pk>[\d]{{1,11}})/b/(?P<b_pk>[\d]{{1,11}})/')
        urls = self.b_router_regex.urls
        self.assertEquals(len(urls), 2)
        self.assertEquals(urls[0].regex.pattern, u'^a/(?P<a_pk>[\d]{1,11})/b/(?P<b_pk>[\d]{1,11})/c/$')
        self.assertEquals(urls[1].regex.pattern, u'^a/(?P<a_pk>[\d]{1,11})/b/(?P<b_pk>[\d]{1,11})/c/(?P<pk>[\d]{1,11})/$')
