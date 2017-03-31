# -*- coding: utf-8 -*-
from __future__ import unicode_literals
__author__ = 'wangyi'


from django.test import SimpleTestCase, TestCase
import json

import logging
from utils.log import LoggerAdaptor
_logger = logging.getLogger("api.tests")

class DynamicQueryRouterTest(SimpleTestCase):

    logger = LoggerAdaptor("TestDynamicQueryRouter", _logger)

    def test_dynamic_query_router(self):
        from router import DefaultDynamicQueryRouter as DefaultNestedRouter
        from viewset import WebSiteViewSet
        nested_router = DefaultNestedRouter(is_method_attached=True)

        nested_router.register(r'website', WebSiteViewSet)

        urls = nested_router.urls
        self.logger.info("router.urls: %s", json.dumps([str(url) for url in urls], sort_keys=True, indent=4))
        self.logger.info("attached methods: %s", json.dumps(nested_router._attached, sort_keys=True, indent=4))
