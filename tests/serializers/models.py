from django.db import models
from rest_framework import serializers, viewsets
from rest_framework_nested import serializers as nested_serializers
from rest_framework_nested import relations


class Parent(models.Model):
    name = models.CharField(max_length=10)


class Child1(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(Parent, related_name='first', on_delete=models.CASCADE)


class Child2(models.Model):
    name = models.CharField(max_length=10)
    root = models.ForeignKey(Parent, related_name='second', on_delete=models.CASCADE)


class GrandChild1(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(Child2, related_name='grand', on_delete=models.CASCADE)


class Child1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Child1
        fields = ('name')


class Child2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Child2
        fields = ('name')


class ParentChild1Serializer(nested_serializers.NestedHyperlinkedModelSerializer):
    class Meta:
        model = Child1
        fields = ('url', 'name')


class ParentChild2GrandChild1Serializer(nested_serializers.NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'parent_pk': 'parent__pk',
        'root_pk': 'parent__root__pk',
    }
    parent = relations.NestedHyperlinkedRelatedField(parent_lookup_kwargs={'root_pk': 'root__pk'},
                                                     view_name='child2-detail', queryset=Child2.objects.all())

    class Meta:
        model = GrandChild1
        fields = ('url', 'name', 'parent')


class ParentChild2Serializer(nested_serializers.NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'root_pk': 'root__pk',
    }

    class Meta:
        model = Child2
        fields = ('url', 'name', 'grand')

    grand = ParentChild2GrandChild1Serializer(
        many=True, read_only=True,
        parent_lookup_kwargs={
            'pk': 'pk',
            'parent_pk': 'parent__pk',
            'root_pk': 'parent__root__pk'
        }
    )


class Parent1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ('name', 'first')

    first = ParentChild1Serializer(many=True, read_only=True)


class Parent2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Parent
        fields = ('name', 'second')

    second = ParentChild2Serializer(many=True, read_only=True)


class Parent1Viewset(viewsets.ModelViewSet):
    serializer_class = Parent1Serializer
    queryset = Parent.objects.all()


class Parent2Viewset(viewsets.ModelViewSet):
    serializer_class = Parent2Serializer
    queryset = Parent.objects.all()


class Child1Viewset(viewsets.ModelViewSet):
    serializer_class = Child1Serializer
    queryset = Child1.objects.all()


class Child2Viewset(viewsets.ModelViewSet):
    serializer_class = Child2Serializer
    queryset = Child2.objects.all()


class ParentChild2GrandChild1Viewset(viewsets.ModelViewSet):
    serializer_class = ParentChild2GrandChild1Serializer
    queryset = GrandChild1.objects.all()
