"""
based upon https://github.com/alanjds/drf-nested-routers/issues/15
"""
from collections import namedtuple

from django.test import TestCase
from django.db import models
from rest_framework.viewsets import ModelViewSet
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter
from rest_framework.response import Response

from tests.helpers import get_regex_pattern


QS = namedtuple('Queryset', ['model'])


class BasicModel(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        app_label = 'testapp'


# DRF 3.8+
try:
    from rest_framework.decorators import action

    def detail_route_decorator(**kwargs):
        return action(detail=True, **kwargs)

    def list_route_decorator(**kwargs):
        return action(detail=False, **kwargs)
except ImportError:
    # for DRF < 3.8
    try:
        from rest_framework.decorators import detail_route as detail_route_decorator, list_route as list_route_decorator
    except ImportError:
        pass


if 'detail_route_decorator' in globals() and 'list_route_decorator' in globals():
    def map_by_name(iterable):
        ret = {}
        for item in iterable:
            ret[item.name] = item
        return ret

    class DetailRouteViewSet(ModelViewSet):
        model = BasicModel
        queryset = QS(BasicModel)

        @detail_route_decorator(methods=["post"])
        def set_password(self, request, pk=None):
            return Response({'hello': 'ok'})

    class ListRouteViewSet(ModelViewSet):
        model = BasicModel
        queryset = QS(BasicModel)

        @list_route_decorator()
        def recent_users(self, request, pk=None):
            return Response([{'hello': 'ok'}])

    class TestNestedSimpleRouter(TestCase):
        def setUp(self):
            self.router = SimpleRouter()
            self.router.register(r'detail', DetailRouteViewSet)
            self.detail_router = NestedSimpleRouter(
                self.router,
                r'detail',
                lookup='detail'
            )
            self.detail_router.register(r'list', ListRouteViewSet)
            self.list_router = NestedSimpleRouter(
                self.detail_router,
                r'list',
                lookup='list'
            )

        def test_dynamic_routes(self):
            self.assertFalse(hasattr(self.router, 'parent_regex'))
            urls = map_by_name(self.router.urls)
            self.assertEquals(
                get_regex_pattern(urls['basicmodel-list']), u'^detail/$'
            )
            self.assertEquals(
                get_regex_pattern(urls['basicmodel-detail']),
                u'^detail/(?P<pk>[^/.]+)/$'
            )
            self.assertEquals(
                get_regex_pattern(urls['basicmodel-set-password']),
                u'^detail/(?P<pk>[^/.]+)/set_password/$'
            )

        def test_nested_parent(self):
            self.assertEqual(
                self.detail_router.parent_regex,
                u'detail/(?P<detail_pk>[^/.]+)/'
            )
            urls = map_by_name(self.detail_router.urls)

            self.assertEquals(
                get_regex_pattern(urls['basicmodel-list']),
                u'^detail/(?P<detail_pk>[^/.]+)/list/$'
            )

            self.assertEquals(
                get_regex_pattern(urls['basicmodel-recent-users']),
                u'^detail/(?P<detail_pk>[^/.]+)/list/recent_users/$'
            )

            self.assertEquals(
                get_regex_pattern(urls['basicmodel-detail']),
                u'^detail/(?P<detail_pk>[^/.]+)/list/(?P<pk>[^/.]+)/$'
            )

        def test_nested_child(self):
            self.assertEqual(
                self.list_router.parent_regex,
                u'detail/(?P<detail_pk>[^/.]+)/list/(?P<list_pk>[^/.]+)/'
            )
