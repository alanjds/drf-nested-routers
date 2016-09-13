from django.db import models
from rest_framework import serializers, viewsets
from rest_framework_nested import serializers as nested_serializers


class Parent(models.Model):
    name = models.CharField(max_length=10)


class Child1(models.Model):
    name = models.CharField(max_length=10)
    parent = models.ForeignKey(Parent, related_name='first')


class Child2(models.Model):
    name = models.CharField(max_length=10)
    root = models.ForeignKey(Parent, related_name='second')


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


class ParentChild2Serializer(nested_serializers.NestedHyperlinkedModelSerializer):
    parent_lookup_url_kwarg = 'root_pk'
    parent_lookup_field = 'root'

    class Meta:
        model = Child2
        fields = ('url', 'name')


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
