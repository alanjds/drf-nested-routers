from collections import namedtuple

from django.conf.urls import include, url
from django.db import models
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import ModelViewSet
from rest_framework_nested.relations import NestedHyperlinkedIdentityField
from rest_framework_nested.routers import NestedSimpleRouter, SimpleRouter

QS = namedtuple('Queryset', ['model'])

factory = APIRequestFactory()


class A(models.Model):
    pass


class ASerializer(HyperlinkedModelSerializer):
    class Meta:
        model = A
        fields = ('b')


class AViewSet(ModelViewSet):
    model = A
    queryset = QS(A)
    serializer_class = ASerializer


class B(models.Model):
    a = models.ForeignKey('A', related_name='bs',
                          related_query_name='b',
                          on_delete=models.CASCADE)


class BSerializer(HyperlinkedModelSerializer):
    url = NestedHyperlinkedIdentityField(
        view_name='b-detail',
        lookup_fields=('a__pk', 'pk')
    )

    class Meta:
        model = B
        fields = (
            'url',
            'a',
        )


class BViewSet(ModelViewSet):
    model = B
    queryset = QS(B)
    serializer_class = BSerializer


class TestNestedHyperlinkedIdentityField(TestCase):
    def setUp(self):
        self.router = SimpleRouter()
        self.router.register(r'a', AViewSet, base_name='a')
        self.a_router = NestedSimpleRouter(self.router, r'a', lookup='a')
        self.a_router.register(r'b', BViewSet, base_name='b')
        self.b_router = NestedSimpleRouter(self.a_router, r'b', lookup='b')
        self.url_patterns = [
            url('', include(self.router.urls)),
            url('', include(self.a_router.urls)),
            url('', include(self.b_router.urls)),
        ]

    def test_nested_url_structure(self):
        with self.settings(ROOT_URLCONF=self.url_patterns):
            detail_url = reverse('b-detail', kwargs={'a_pk': 1, 'pk': 2})
            list_url = reverse('b-detail', kwargs={'a_pk': 1})
        self.assertEqual(detail_url, '/a/1/b/2/')
        self.assertEqual(list_url, '/a/1/b/')

    def test_nested_identity_field(self):
        with self.settings(ROOT_URLCONF=self.url_patterns):
            request = factory.get('/', '', content_type='application/json')
            bview = BViewSet.as_view(actions={'get': 'list'})
            response = bview(request)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
