**This is a work in progress. It "works for me" at www.apiregistro.com.br,
but I cannot warranty that it fully "works everywhere" yet. Join us on Gitter (below) if you need some help.**

# drf-nested-routers

[![Join the chat at https://gitter.im/alanjds/drf-nested-routers](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/alanjds/drf-nested-routers?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Build Status](https://travis-ci.org/alanjds/drf-nested-routers.svg?branch=master)](https://travis-ci.org/alanjds/drf-nested-routers)

This package provides routers and fields to create nested resources in the [Django Rest Framework](http://django-rest-framework.org/)

Nested resources are needed for full REST URL structure, if one resource lives inside another.

The following example is about Domains and DNS Nameservers.
There are many domains, and each domain has many nameservers. The "nameserver" resource does not
exist without a domain, so you need it "nested" inside the domain.


## Requirements & Compatibility

-  Python (3.5, 3.6, 3.7)
-  Django (1.11, 2.0, 2.1, 2.2, 3.0)
-  Django REST Framework (3.6, 3.7, 3.8, 3.9, 3.10)


## Installation

You can install this library using pip:

```pip install drf-nested-routers```


## Quickstart

The desired URL signatures are:
```
/domain/ <- Domains list
/domain/{pk}/ <- One domain, from {pk}
/domain/{domain_pk}/nameservers/ <- Nameservers of domain from {domain_pk}
/domain/{domain_pk}/nameservers/{pk} <- Specific nameserver from {pk}, of domain from {domain_pk}
```

How to do it (example):
```python
# urls.py
from rest_framework_nested import routers
from views import DomainViewSet, NameserverViewSet
(...)

router = routers.SimpleRouter()
router.register(r'domains', DomainViewSet)

domains_router = routers.NestedSimpleRouter(router, r'domains', lookup='domain')
domains_router.register(r'nameservers', NameserverViewSet, base_name='domain-nameservers')
# 'base_name' is optional. Needed only if the same viewset is registered more than once
# Official DRF docs on this option: http://www.django-rest-framework.org/api-guide/routers/

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^', include(domains_router.urls)),
)
```
```python
# views.py

## For Django' ORM-based resources ##

class NameserverViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Nameserver.objects.filter(domain=self.kwargs['domain_pk'])

## OR: non-ORM resources ##

class NameserverViewSet(viewsets.ViewSet):
    def list(self, request, domain_pk=None):
        nameservers = self.queryset.filter(domain=domain_pk)
        (...)
        return Response([...])

    def retrieve(self, request, pk=None, domain_pk=None):
        nameservers = self.queryset.get(pk=pk, domain=domain_pk)
        (...)
        return Response(serializer.data)
```


## Advanced

### Hyperlinks for Nested resources

**(optional)** If you need hyperlinks for nested relations, you need a custom serializer.
```python
# serializers.py
# (needed only if you want hyperlinks for nested relations on API)
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

class DomainSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Domain

    nameservers = HyperlinkedIdentityField(
        view_name='domain-nameservers-list',
        lookup_url_kwarg='domain_pk'
    )

	## OR ##

    nameservers = NestedHyperlinkedRelatedField(
        many=True,
        read_only=True,   # Or add a queryset
        view_name='domain-nameservers-detail',
        parent_lookup_kwargs={'domain_pk': 'domain__pk'}
    )
```

**(optional)** If you want a little bit more control over the fields displayed for the nested relations while looking at the parent, you need a custom serializer using NestedHyperlinkedModelSerializer.
```python
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

class NameserverSerializers(HyperlinkedModelSerializer):
	class Meta:
		model = Nameserver
		fields = (...)


class DomainNameserverSerializers(NestedHyperlinkedModelSerializer):
	parent_lookup_kwargs = {
		'domain_pk': 'domain__pk',
	}
	class Meta:
		model = Nameserver
		fields = ('url', ...)


class DomainSerializer(HyperlinkedModelSerializer):
	class Meta:
		model = Domain
		fields = (..., 'nameservers')

	nameservers = DomainNameserverSerializers(many=True, read_only=True)
```

### Infinite-depth Nesting

Example of nested router 3 levels deep.  You can use this same logic to nest routers as deep as you need.  This example accomplishes the below URL patterns.
```
/clients/
/clients/{pk}/
/clients/{client_pk}/maildrops/
/clients/{client_pk}/maildrops/{maildrop_pk}/
/clients/{client_pk}/maildrops/{maildrop_pk}/recipients/
/clients/{client_pk}/maildrops/{maildrop_pk}/recipients/{pk}/
```

```python
# urls.py
router = DefaultRouter()
router.register(r'clients', ClientViewSet, base_name='clients')

client_router = routers.NestedSimpleRouter(router, r'clients', lookup='client')
client_router.register(r'maildrops', MailDropViewSet, base_name='maildrops')

maildrops_router = routers.NestedSimpleRouter(client_router, r'maildrops', lookup='maildrop')
maildrops_router.register(r'recipients', MailRecipientViewSet, base_name='recipients')

urlpatterns = patterns (
    '',
    url(r'^', include(router.urls)),
    url(r'^', include(client_router.urls)),
    url(r'^', include(maildrops_router.urls)),
)
```

```python
# views.py
class ClientViewSet(viewsets.ViewSet):
    serializer_class = ClientSerializer

    def list(self, request,):
        queryset = Client.objects.filter()
        serializer = ClientSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Client.objects.filter()
        client = get_object_or_404(queryset, pk=pk)
        serializer = ClientSerializer(client)
        return Response(serializer.data)

class MailDropViewSet(viewsets.ViewSet):
    serializer_class = MailDropSerializer

    def list(self, request, client_pk=None):
        queryset = MailDrop.objects.filter(client=client_pk)
        serializer = MailDropSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, client_pk=None):
        queryset = MailDrop.objects.filter(pk=pk, client=client_pk)
        maildrop = get_object_or_404(queryset, pk=pk)
        serializer = MailDropSerializer(maildrop)
        return Response(serializer.data)

class MailRecipientViewSet(viewsets.ViewSet):
    serializer_class = MailRecipientSerializer

    def list(self, request, client_pk=None, maildrop_pk=None):
        queryset = MailRecipient.objects.filter(mail_drop__client=client_pk, mail_drop=maildrop_pk)
        serializer = MailRecipientSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, client_pk=None, maildrop_pk=None):
        queryset = MailRecipient.objects.filter(pk=pk, mail_drop=maildrop_pk, mail_drop__client=client_pk)
        maildrop = get_object_or_404(queryset, pk=pk)
        serializer = MailRecipientSerializer(maildrop)
        return Response(serializer.data)
```

## Testing

In order to get started with testing, you will need to install [tox](https://tox.readthedocs.io/en/latest/).
Once installed, you can then run one environment locally, to speed up your development cycle:

```
$ tox -e py37-django2.2-drf3.9
```

Once you submit a pull request, your changes will be run against many environments with Travis CI.


## License

This package is licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
and can undestand more at http://choosealicense.com/licenses/apache/ on the
sidebar notes.

Apache Licence v2.0 is a MIT-like licence. This means, in plain English:
- It's truly open source
- You can use it as you wish, for money or not
- You can sublicence it (change the licence!!)
- This way, you can even use it on your closed-source project
As long as:
- You cannot use the authors name, logos, etc, to endorse a project
- You keep the authors copyright notices where this code got used, even on your closed-source project
(come on, even Microsoft kept BSD notices on Windows about its TCP/IP stack :P)
