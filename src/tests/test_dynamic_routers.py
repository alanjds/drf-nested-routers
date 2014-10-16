"""
based upon https://github.com/alanjds/drf-nested-routers/issues/15
"""
from django.test import TestCase
from rest_framework.viewsets import ModelViewSet
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter
from rest_framework.response import Response
from testapp.models import BasicModel

try:
    from rest_framework.decorators import detail_route, list_route
except ImportError:
    pass
else:
    def map_by_name(iterable):
        ret = {}
        for item in iterable:
            ret[item.name] = item
        return ret

    class DetailRouteViewSet(ModelViewSet):
        model = BasicModel

        @detail_route(methods=["post"])
        def set_password(self, request, pk=None):
            return Response({'hello': 'ok'})

    class ListRouteViewSet(ModelViewSet):
        model = BasicModel

        @list_route()
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
                urls['basicmodel-list'].regex.pattern, u'^detail/$'
            )
            self.assertEquals(
                urls['basicmodel-detail'].regex.pattern,
                u'^detail/(?P<pk>[^/]+)/$'
            )
            self.assertEquals(
                urls['basicmodel-set-password'].regex.pattern,
                u'^detail/(?P<pk>[^/]+)/set_password/$'
            )

        def test_nested_parent(self):
            self.assertEqual(
                self.detail_router.parent_regex,
                u'detail/(?P<detail_pk>[^/]+)/'
            )
            urls = map_by_name(self.detail_router.urls)

            self.assertEquals(
                urls['basicmodel-list'].regex.pattern,
                u'^detail/(?P<detail_pk>[^/]+)/list/$'
            )

            self.assertEquals(
                urls['basicmodel-recent-users'].regex.pattern,
                u'^detail/(?P<detail_pk>[^/]+)/list/recent_users/$'
            )

            self.assertEquals(
                urls['basicmodel-detail'].regex.pattern,
                u'^detail/(?P<detail_pk>[^/]+)/list/(?P<pk>[^/]+)/$'
            )

        def test_nested_child(self):
            self.assertEqual(
                self.list_router.parent_regex,
                u'detail/(?P<detail_pk>[^/]+)/list/(?P<list_pk>[^/]+)/'
            )
