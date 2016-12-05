from django.conf.urls import url, include
from rest_framework_nested import routers

from tests.serializers.models import Parent1Viewset, Child1Viewset, Parent2Viewset, Child2Viewset, ParentChild2GrandChild1Viewset


router_1 = routers.SimpleRouter()
router_1.register('parent1', Parent1Viewset, base_name='parent1')
parent_1_router = routers.NestedSimpleRouter(router_1, r'parent1', lookup='parent')
parent_1_router.register(r'child1', Child1Viewset, base_name='child1')

router_2 = routers.SimpleRouter()
router_2.register('parent2', Parent2Viewset, base_name='parent2')
parent_2_router = routers.NestedSimpleRouter(router_2, r'parent2', lookup='root')
parent_2_router.register(r'child2', Child2Viewset, base_name='child2')

parent_2_grandchild_router = routers.NestedSimpleRouter(parent_2_router, r'child2', lookup='parent')
parent_2_grandchild_router.register(r'grandchild1', ParentChild2GrandChild1Viewset, base_name='grandchild1')

urlpatterns = [
    url(r'^', include(router_1.urls)),
    url(r'^', include(parent_1_router.urls)),
    url(r'^', include(router_2.urls)),
    url(r'^', include(parent_2_router.urls)),
    url(r'^', include(parent_2_grandchild_router.urls)),
]
