**This is a work in progress. It "works for me" at www.apiregistro.com.br, 
but I cannot warranty that it fully "works everywhere" yet.**

drf-nested-routers
=====================

This package provides routers and relations to create nested resources in the [Django Rest Framework](http://django-rest-framework.org/)

Nested resources are needed for full REST URL structure, if one resource lives inside another.

The following example is about Domains and DNS Nameservers. 
There is many domains, and each have many nameservers. The "nameserver" resource does not
exist without a domain, so you need it "nested" inside the domain.

Installation
------------

You can install this library using pip:

```pip install drf-nested-routers```

Quickstart
----------

The desired URL signatures are:
```
\domain\ <- Domains list
\domain\{pk}\ <- One domain, from {pk]
\domain\{domain_pk}\nameservers\ <- Nameservers of domain from {domain_pk}
\domain\{domain_pk}\nameservers\{pk} <- Specific nameserver from {pk}, of domain from {domain_pk}
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
domains_router.register(r'nameservers', NameserverViewSet)

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^', include(domains_router.urls)),
)
```

License
=======

This package is licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
and can undestand more at http://choosealicense.com/licenses/apache/ on the
sidebar notes.

Apache Licence v2.0 is a MIT-like licence. This means, in plain English:
- Its trully open source
- You can use it as you wish, for money or not
- You can sublicence it (change the licence!!)
- This way, you can even use it on your closed-source project
As long as:
- You cannot use the authors name, logos, etc, to endorse a project
- You keep the authors copyright notices where this code got used, even on your closed-source project
(come on, even Microsoft kept BSD notices on Windows about its TCP/IP stack :P)
