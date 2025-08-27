import json

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import RequestFactory, TestCase, override_settings
from django.urls import include, path, reverse
from rest_framework import status
from rest_framework.reverse import reverse as drf_reverse
from rest_framework.routers import SimpleRouter
from rest_framework.schemas import generators
from rest_framework.serializers import HyperlinkedModelSerializer, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from rest_framework_nested.routers import NestedSimpleRouter
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.viewsets import NestedViewSetMixin

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

router.register('root', RootViewSet, basename='root')
root_router = NestedSimpleRouter(router, r'root', lookup='parent')
root_router.register(r'child', ChildViewSet, basename='child')
root_router.register(r'child-with-nested-mixin', ChildWithNestedMixinViewSet, basename='child-with-nested-mixin')
root_router.register(r'child-with-nested-mixin-in-view', ChildWithNestedMixinViewSetDefinedInViewset, basename='child-with-nested-mixin-in-view')
root_router.register(r'child-with-nested-mixin-not-defined', ChildWithNestedMixinViewSetWithoutParentKwargs, basename='child-with-nested-mixin-not-defined')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(root_router.urls)),
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
        self.root_2_child_c = Child.objects.create(name='root-2-child-c', parent=self.root_2)

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

        self.assertEqual(len(data), 3)

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

    def test_create_child_on_viewset_with_mixin(self):
        """
        The `ViewSet` that uses `NestedViewSetMixin` automatically sets the
        parent kwarg on the request.{data,query_params} querydict.

        This allows the parent lookup arg to _not_ be provided on the POST
        data, as is already provided as part of the URL.
        """
        resource_url = reverse('child-with-nested-mixin-list',
                               kwargs={'parent_pk': self.root_1.pk})

        response = self.client.post(resource_url,
                                    content_type='application/json',
                                    data=json.dumps({
                                        'name': 'New Child',
                                    }))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = json.loads(response.content.decode())

        self.assertEqual(data['name'], 'New Child')
        parent_url = drf_reverse('root-detail',
                                 kwargs={'pk': self.root_1.pk},
                                 request=response.wsgi_request)
        self.assertEqual(data['parent'], parent_url)

    def test_get_queryset_for_children_resource(self):
        gen = generators.BaseSchemaGenerator()
        gen._initialise_endpoints()
        for path, method, callback in gen.endpoints:
            view = gen.create_view(callback, method)
            # drf_yasg set swagger_fake_view attribute for all view
            setattr(view, 'swagger_fake_view', True)
            # no error message should be raised here
            view.get_queryset()

    def test_create_invalid_data_with_mixin(self):
        """
        The `NestedViewSetMixin` automatically sets the
        parent kwarg on the request.{data,query_params} querydict.

        This happens in the `initialize_request()` lifecycle method, but
        this method is outside the DRF exception handler's scope, so
        when the `request.data` is accessed, if the data is invalid, then
        the exception will not be handled by DRF, and it will result in a 500.

        If we handle that after the `initial()` method, which checks all
        the API policies, like content negotiation, throttling, permisisons, etc, then
        the invalid data will be caught by the content negotiation and an appropiate
        HTTP 400 error should be received by the client.
        """
        resource_url = reverse(
            "child-with-nested-mixin-list", kwargs={"parent_pk": self.root_1.pk}
        )

        response = self.client.post(
            resource_url, content_type="application/json", data="invalid json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"detail": "JSON parse error - Expecting value: line 1 column 1 (char 0)"},
        )
