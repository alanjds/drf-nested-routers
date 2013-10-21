**This is a work in progress. It "works for me" at www.apiregistro.com.br, 
but I cannot warranty that it fully "works everywhere" yet.**

rest_framework_nested
=====================

This package provides routers and relations to create nested resources in the
Django Rest Framework

Example:

```python
# urls.py

from rest_framework_nested import routers

router = routers.SimpleRouter()
router.register(r'domains', DomainViewSet)

domains_router = routers.NestedSimpleRouter(router, r'domains', lookup='domain')
domains_router.register(r'nameservers', NameserverViewSet)

url_patterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^', include(domains_router.urls)),
)

urlpatterns = router.urls
```
