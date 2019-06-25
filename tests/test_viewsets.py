import json

from django.conf.urls import url, include
from django.db import models
from django.test import TestCase, override_settings, RequestFactory
from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.routers import SimpleRouter
from rest_framework.serializers import HyperlinkedModelSerializer, ModelSerializer
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


class ChildSerializerWithoutParentKwargs(ModelSerializer):
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

class ChildWithNestedMixinViewSetDefinedInViewset(NestedViewSetMixin, ModelViewSet):
    parent_lookup_kwargs = {
        'parent_pk': 'parent__pk'
    }
    """Identical to `ChildViewSet` but with the mixin."""
    serializer_class = ChildSerializerWithoutParentKwargs
    queryset = Child.objects.all()

class ChildWithNestedMixinViewSetWithoutParentKwargs(NestedViewSetMixin, ModelViewSet):
    """Identical to `ChildViewSet` but with the mixin."""
    serializer_class = ChildSerializerWithoutParentKwargs
    queryset = Child.objects.all()

router = SimpleRouter()
router.register('root', RootViewSet, base_name='root')
root_router = NestedSimpleRouter(router, r'root', lookup='parent')
root_router.register(r'child', ChildViewSet, base_name='child')
root_router.register(r'child-with-nested-mixin', ChildWithNestedMixinViewSet, base_name='child-with-nested-mixin')
root_router.register(r'child-with-nested-mixin-in-view', ChildWithNestedMixinViewSetDefinedInViewset, base_name='child-with-nested-mixin-in-view')
root_router.register(r'child-with-nested-mixin-not-defined', ChildWithNestedMixinViewSetWithoutParentKwargs, base_name='child-with-nested-mixin-not-defined')


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

    def test_nested_child_viewset(self):
        """
        The regular `ViewSet` that does not take the parents into account. The
        `QuerySet` consists of all `Child` objects.

        We request all children "from root 1". In return, we get all children,
        from both root 1 and root 2.
        """
        url = reverse('child-list', kwargs={'parent_pk': self.root_1.pk,})

        response = self.client.get(url, content_type='application/json')
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
        url = reverse('child-with-nested-mixin-list', kwargs={'parent_pk': self.root_1.pk})

        response = self.client.get(url, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content.decode())

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], self.root_1_child_a.name)

    def test_nested_child_viewset_with_mixin_in_view(self):
        """
        The `ViewSet` that uses the `NestedViewSetMixin` filters the
        `QuerySet` to only those objects that are attached to its parent.

        We request all children "from root 1". In return, we get only the
        children from root 1.
        """
        url = reverse('child-with-nested-mixin-in-view-list', kwargs={'parent_pk': self.root_1.pk})

        response = self.client.get(url, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = json.loads(response.content.decode())

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], self.root_1_child_a.name)

    def test_nested_child_viewset_with_mixin_not_defined(self):
        """
        The `ViewSet` that uses the `NestedViewSetMixin` filters the
        `QuerySet` to only those objects that are attached to its parent.

        We request all children "from root 1". In return, we get only the
        children from root 1.
        """
        url = reverse('child-with-nested-mixin-not-defined-list', kwargs={'parent_pk': self.root_1.pk})

        with self.assertRaises(ImproperlyConfigured):
            response = self.client.get(url, content_type='application/json')
