**This is a work in progress, and it does not fully work yet.**

rest_framework_nested
=====================

This package provides routers and relations to create nested resources in the
Django Rest Framework

Example:

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

        router = routers.DefaultRouter()
        router.register('users', UserViewSet, 'user')
        router.register('accounts', AccountViewSet, 'account')

        urlpatterns = router.urls
