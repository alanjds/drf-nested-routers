from __future__ import unicode_literals
__author__ = 'wangyi'

import json
from ..third_party.models import WebSite, Headline
from utils import parser
from ..third_party.serializer import WebSiteSerializer, HeadlineSerializer, \
    SerializerManager
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import generics, filters
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from utils.v_utils import get_args_by_req
from utils.exceptions import handle_exc, BAD_SIGN, Cols_Not_Found

import logging
from utils.log import LoggerAdaptor
_logger = logging.getLogger("api.tests")


class NestedViewRouter(generics.GenericAPIView):

    # authentication_classes = (SignatureAuth, TokenAuthentication, )

    _LIMIT = 1000
    PAGINATION_DEF = 10

    query_set = None
    serializer_class = None

    logger = LoggerAdaptor("analyse_dynamic_runtime", _logger)

    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    exclude_from_selector_fields = (u'ordering', u'search', u'offset', u'limit', u'fields',
                                    u'format', u'key', u'signature', u'url', u'date', u'request_target',
                                    u'next_url')
    sign, cols = None, None
    query_key = 'pk'

    @property
    def _req_method(self):
        return self.request.method.lower()

    def dispatch(self, request,
                 *args, **kwargs):
        """
        `.dispatch()` is pretty much the same as Django_Rest's regular dispatch,
        but with extra hooks for filtering,  extracting, and pagination.
        """
        # substitute => initialize_request
        # return a request in order to be used by viewset.initial_request
        request = self._init_req(request)
        self.headers = self.default_response_headers  # deprecate?

        try:
            self.initial(request, *args, **kwargs)
            # Get the appropriate handler method
            handler = getattr(self, self._req_method, self.http_method_not_allowed) \
                if self._req_method in self.http_method_names else \
                self.http_method_not_allowed

            # from dill.source import getsource
            # self.logger.info(getsource(handler))
            # https://www.ibm.com/developerworks/cn/linux/l-cn-pythondebugger/
            self.logger.info(handler)
            # pdb.set_trace()
            # analyse source codes
            response = handler(request, *args, **kwargs)

        except Exception as exc:
            # pdb.pm()
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response

    def _init_req(self, request):
        self.query_params = get_args_by_req(request)
        parser_context = self.get_parser_context(request)

        self.request = Request(request, parsers=self.get_parsers(), parser_context=parser_context,
                               authenticators=self.get_authenticators(),
                               negotiator=self.get_content_negotiator())
        return self.request
    # hook to initialize_request
    initialize_request = _init_req

    def only_cols(self, query_set, fields_string):
        sign, cols = parser.field_parse(fields_string)
        query_set = query_set.only(*cols) if sign == '+' else query_set.defer(*cols)
        self.sign, self.cols = sign, cols
        return query_set

    # override the original mehtod to perform magic filtering
    def get_queryset(self, query_set=None, serializer_class=None):

        if query_set is None:
            _qs = super(NestedViewRouter, self).get_queryset()
            query_set = _qs

        query_set = self.filter_queryset(query_set)
        selector_args = {}

        # filtering fields on serializer
        def get_valid_fields(serializer_class):
            valid_fields = [
                field.source or field_name
                for field_name, field in serializer_class().fields.items()
                if not getattr(field, 'write_only', False) and not field.source == '*'
            ]
            return valid_fields

        if serializer_class is None:
            serializer_class = self.serializer_class

        valid_fields = get_valid_fields(serializer_class)
        limit = self._LIMIT
        for k, v in self.query_params.items():
            if k not in self.exclude_from_selector_fields and \
                    k in valid_fields:
                selector_args[k] = v

            elif k == u'offset':
                limit = int(v) + limit

            elif k == u'fields':
                try:
                    query_set = self.only_cols(query_set, v)
                except Cols_Not_Found as err:
                    err.detail = """
                    Available Fields: %s
                    """ % json.dump(valid_fields, sort_keys=True, indent=4)
                    raise err
                except BAD_SIGN as err:
                    err.detail = """
                    Available Signs: %s
                    """ % ('+', '-')
        self._slicer = slice(0, limit)
        query_set = query_set.filter(**selector_args)
        return query_set

    def get_args(self):
        return (self.args, self.kwargs)

    def get_object(self, req, pk):
        selector_args = get_args_by_req(req, f=_extract_args)
        query_set = self.get_queryset().filter(**selector_args)
        label = self.query_key
        selector_args[label] = pk
        ob = query_set(**selector_args)
        return ob

    def get_object_plural(self, req, pk=None):  # plural
        selector_args = get_args_by_req(req, f=_extract_args)
        if pk is not None:
            query_set = self.get_queryset().filter(**selector_args)
            label = self.query_key
            __code = "query_set=query_set.filter({pk}='{val}', **selector_args)"
            exec(__code.format(pk=label, val=pk))
            query_set = query_set.__getitem__(self._slicer)
        else:
            query_set = self.get_queryset() \
                            .filter(**selector_args) \
                            .__getitem__(self._slicer)
        # .order_by('-{query_key}'.format(query_key=self.query_key))\
        page = self.paginate_queryset(query_set)
        return page

    def get_response(self, req, pk=None):

        def group(req):
            page = self.get_object_plural(req)
            repr = self.serializer(page, many=True)
            if hasattr(repr, '__len__') and \
                    len(repr) < self.PAGINATION_DEF:
                return Response(data=repr)
            else:
                return self.get_paginated_response(data=repr)

        def ins(req, pk):

            query_set = self.get_object(req, pk)
            repr = self.serializer(query_set)
            return Response(repr)

        try:
            if not pk:
                rep = group(req)
            else:
                rep = ins(req, pk)
        except Exception as err:
            import traceback
            traceback.print_exc()
            return handle_exc(None,
                              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                              details=err.message)
        return rep


def _extract_args(args):
    black_list = NestedViewRouter.exclude_from_selector_fields
    return {k: v for k, v in args.items() if k.lower() not in black_list}


class HeadlineViewRouter(NestedViewRouter):

    queryset = Headline.objects.all()
    serializer_class = HeadlineSerializer
    serializer = SerializerManager(HeadlineSerializer)

    ordering_fields = ('post_date', 'title', 'digest', 'score')

    search_fields = ('id', 'post_date', 'title', 'digest', 'website_id')
    query_key = 'title'

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_headlines(self, req):
        return self.get_response(req)

    def get_headline_by_title(self, req, title):
        return self.get_response(req, title)


class WebSiteViewRouter(NestedViewRouter):

    queryset = WebSite.objects.all()
    serializer_class = WebSiteSerializer
    serializer = SerializerManager(WebSiteSerializer)

    ordering_fields = ('id', 'name',)

    search_fields = ('id', 'name',)
    query_key = 'name'

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_websites(self, req):
        return self.get_response(req)

    def get_website_by_name(self, req, name):
        return self.get_response(req, name)

    def create_website_by_name(self, req, name, **param):
        url = req.query_params.get("url", '')
        tags = req.query_params.get("tags", '')

        if url is '' or tags is '':
            return handle_exc(None,
                              status_code=status.HTTP_400_BAD_REQUEST, details="Not enough parameters")

        website = WebSite.objects.get(name=name)
        if len(website) == 0:
            website = WebSite(name=name, url=url, tags=tags)
            website.save()
        else:
            website = website[0]

        serialized = WebSiteSerializer(website)
        return Response(data=serialized.data, status=status.HTTP_201_CREATED,
                        headers={'Location': serialized.data.get('url', None)})

    def update_partially_website_by_name(self, req, name, **param):
        pass

    def delete_website_by_name(self, req, name):
        wb = WebSite.objects.filter(name=name)
        if len(wb) == 0:
            return handle_exc(None,
                              status_code=status.HTTP_400_BAD_REQUEST, details="Not exist!")
        data = WebSiteSerializer(wb, many=True).data
        wb.delete()
        return Response(data=data, status=status.HTTP_204_NO_CONTENT)

    update_website_by_name = get_website_by_name
