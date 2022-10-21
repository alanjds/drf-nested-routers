from django.urls import include, path
from rest_framework_nested import routers

from tests.serializers.models import Parent1Viewset, Child1Viewset, Parent2Viewset, Child2Viewset, ParentChild2GrandChild1Viewset


router_1 = routers.SimpleRouter()
router_1.register('parent1', Parent1Viewset, basename='parent1')
parent_1_router = routers.NestedSimpleRouter(router_1, r'parent1', lookup='parent')
parent_1_router.register(r'child1', Child1Viewset, basename='child1')

router_2 = routers.SimpleRouter()
router_2.register('parent2', Parent2Viewset, basename='parent2')
parent_2_router = routers.NestedSimpleRouter(router_2, r'parent2', lookup='root')
parent_2_router.register(r'child2', Child2Viewset, basename='child2')

parent_2_grandchild_router = routers.NestedSimpleRouter(parent_2_router, r'child2', lookup='parent')
parent_2_grandchild_router.register(r'grandchild1', ParentChild2GrandChild1Viewset, basename='grandchild1')

urlpatterns = [
    path('', include(router_1.urls)),
    path('', include(parent_1_router.urls)),
    path('', include(router_2.urls)),
    path('', include(parent_2_router.urls)),
    path('', include(parent_2_grandchild_router.urls)),
]
