from django.conf.urls import url, include
from rest_framework_nested import routers

from tests.serializers.models import Parent1Viewset, Child1Viewset, Parent2Viewset, Child2Viewset, Parent3Viewset


router_1 = routers.SimpleRouter()
router_1.register('parent1', Parent1Viewset, base_name='parent1')
parent_1_router = routers.NestedSimpleRouter(router_1, r'parent1', lookup='parent')
parent_1_router.register(r'child1', Child1Viewset, base_name='child1')

router_2 = routers.SimpleRouter()
router_2.register('parent2', Parent2Viewset, base_name='parent2')
parent_2_router = routers.NestedSimpleRouter(router_2, r'parent2', lookup='root')
parent_2_router.register(r'child2', Child2Viewset, base_name='child2')

router_3 = routers.SimpleRouter()
router_3.register('parent3', Parent3Viewset, base_name='parent3')
parent_3_router = routers.NestedSimpleRouter(router_3, r'parent3', lookup='parent')
parent_3_router.register(r'child1', Child1Viewset, base_name='parent3-child1')
parent_3_router2 = routers.NestedSimpleRouter(router_3, r'parent3', lookup='root')
parent_3_router2.register(r'child2', Child2Viewset, base_name='parent3-child2')

urlpatterns = [
    url(r'^', include(router_1.urls)),
    url(r'^', include(parent_1_router.urls)),
    url(r'^', include(router_2.urls)),
    url(r'^', include(parent_2_router.urls)),
    url(r'^', include(router_3.urls)),
    url(r'^', include(parent_3_router.urls)),
    url(r'^', include(parent_3_router2.urls))
]
