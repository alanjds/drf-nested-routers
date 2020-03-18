import json

from django.conf.urls import url, include
from django.db import models
from django.test import TestCase, override_settings, RequestFactory
from rest_framework import status
from rest_framework.routers import SimpleRouter
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ModelViewSet

from rest_framework_nested.routers import NestedSimpleRouter
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.viewsets import NestedViewSetMixin

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


factory = RequestFactory()


class Root(models.Model):
    name = models.CharField(max_length=255)


class Child(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(Root, on_delete=models.CASCADE)


class RootSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Root
        fields = ('name', 'children', 'children_with_nested_mixin')


class ChildSerializer(NestedHyperlinkedModelSerializer):
    class Meta:
        model = Child
        fields = ('name', 'parent', )


class RootViewSet(ModelViewSet):
    serializer_class = RootSerializer
    queryset = Root.objects.all()


class ChildViewSet(ModelViewSet):
    serializer_class = ChildSerializer
    queryset = Child.objects.all()


class ChildWithNestedMixinViewSet(NestedViewSetMixin, ModelViewSet):
    """Identical to `ChildViewSet` but with the mixin."""
    serializer_class = ChildSerializer
    queryset = Child.objects.all()


router = SimpleRouter()
router.register('root', RootViewSet, basename='root')
root_router = NestedSimpleRouter(router, r'root', lookup='parent')
root_router.register(r'child', ChildViewSet, basename='child')
root_router.register(r'child-with-nested-mixin', ChildWithNestedMixinViewSet, basename='child-with-nested-mixin')


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(root_router.urls)),
]


@override_settings(ROOT_URLCONF=__name__)
class TestNestedSimpleRouter(TestCase):
    def setUp(self):
        """
        We look at the same data but with different `ViewSet`s. One regular
        `ViewSet` and one using the mixin to filter the children based on its
        parent(s).

        Simple setup:

        root 1
        |
        +-- child a

        root 2
        |
        +-- child b
        """

        self.root_1 = Root.objects.create(name='root-1')
        self.root_2 = Root.objects.create(name='root-2')
        self.root_1_child_a = Child.objects.create(name='root-1-child-a', parent=self.root_1)
        self.root_2_child_b = Child.objects.create(name='root-2-child-b', parent=self.root_2)

        self.root_1_detail_url = reverse('root-detail', kwargs={'pk': self.root_1.pk})

        self.root_1_child_list_url = reverse('child-list', kwargs={
            'parent_pk': self.root_1.pk,
        })
        self.root_1_child_with_nested_mixin_list_url = reverse('child-with-nested-mixin-list', kwargs={
            'parent_pk': self.root_1.pk,
        })

    def test_nested_child_viewset(self):
        """
        The regular `ViewSet` that does not take the parents into account. The
        `QuerySet` consists of all `Child` objects.

        We request all children "from root 1". In return, we get all children,
        from both root 1 and root 2.
        """
        response = self.client.get(self.root_1_child_list_url, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content.decode())

        self.assertEqual(len(data), 2)

    def test_nested_child_viewset_with_mixin(self):
        """
        The `ViewSet` that uses the `NestedViewSetMixin` filters the
        `QuerySet` to only those objects that are attached to its parent.

        We request all children "from root 1". In return, we get only the
        children from root 1.
        """
        response = self.client.get(self.root_1_child_with_nested_mixin_list_url, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content.decode())

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], self.root_1_child_a.name)
