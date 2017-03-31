__author__ = 'wangyi'

from rest_framework.viewsets import ViewSetMixin
from views import WebSiteViewRouter, HeadlineViewRouter


class WebSiteViewSet(ViewSetMixin,
                     WebSiteViewRouter):

    verbose_key = 'website'
    prefix_abbr = 'ws'

    affiliates = ['headline']


class HeadlineViewSet(ViewSetMixin,
                      HeadlineViewRouter):

    verbose_key = 'headline'
    prefix_abbr = 'hl'
