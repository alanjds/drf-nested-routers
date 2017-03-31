Quick Start
-----------

The historical approaches to "nested routers" can be devided into two categries:
1) First proposed in Microsoft .net asp framework, aka users explicitly specify the relationship between resources. Hence,
it also requires developers to implement their corresponding view methods to handle the relationship queries.
2) In RESTful scheme, we rarely concern about the relationship but refines the relationship in logics. i.e we have resources "A", then we define CRUD operations upon it using query key or looking up key. The relationships maintained by develpers' logics.


Hence this broughts redundancies for a fast and hight level templated programmes. Here I proposed another approach, as far as I concerned, no people really use it. Please update the historical approaches to let me know.

The plan is :
> relationship is actually a tree based concept. We have foreign keys for children to find their parents, and what if we have some tools to help parents to list their children?
We also need "inferring engine" to deal with the problems like "A's Parent's child' uncle C, what is the relationship between A & C" (in progress, I am working AI problems) 

i.e 
> a url like "parent/childB/blablabla" can be converted by engine as "childB/blablabla/?query\_key=constrained\_by\_`parent`"
The process is a finite states machine if we have the relationship graph.

Hence it is the users' responsibility to specify the path from parent to children in viewsets like:
```python
class WebSiteViewSet(ViewSetMixin,
                    WebSiteViewRouter):

    verbose_key = 'website'
    prefix_abbr = 'ws'

    affiliates = ['headline',]

class HeadlineViewSet(ViewSetMixin,
                    HeadlineViewRouter):

    verbose_key = 'headline'
    prefix_abbr = 'hl'
```

The programme should deduce a mehtod to convert the relationship so that it is totally methods already hanlded by children 
I currently use "Redirect" method to land the proposal, and it happens inside server. In my last tests, it works.

A user can simply specify the in relationship in two files:
1. viewset.py (illustrated above)
2. urls.py:
```python
from router import DefaultDynamicQueryRouter as DefaultNestedRouter
from viewset import WebSiteViewSet
nested_router = DefaultNestedRouter(is_method_attached=True)
nested_router.register(r'website', WebSiteViewSet)

urlpatterns += patterns('',
    url(r'^api/{v:}/'.format(v=VERSION), include(nested_router.urls)),
)
```


Testing
=======
I use django test services, simply run
```
python test_main.py
```    
You can checkout the result in tests/nested\_router.out
