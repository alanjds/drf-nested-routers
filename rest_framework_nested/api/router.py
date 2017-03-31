from __future__ import unicode_literals

__author__ = 'wangyi'

import json

from collections import OrderedDict, namedtuple
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import NoReverseMatch
from django.conf.urls import url

from rest_framework.routers import SimpleRouter
from rest_framework.routers import flatten
from rest_framework.response import Response
from rest_framework import views
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns

import logging
from utils.log import LoggerAdaptor
_logger = logging.getLogger("api.router")

TYPE_RE = u"(?P<{type}>[a-z0-9_][a-z0-9\s_]+?)"
QUERY_KEY_RE = u"(?P<{query_key}>[a-z0-9_\s\w\uff1f]+|[\u4e00-\u9fa5\uff1f]+|[^\x00-\xff]+)" # ^(?!accounts$)
RESOURCE_NAME_RE = u"(?P<resource_name>[^a-z0-9_\s\w\uff1f]+|[\u4e00-\u9fa5\uff1f]+|[^\x00-\xff]+)"
RESOURCE_QK_RE = u"(?P<res_query_key>[a-z0-9_\s\w\uff1f]+|[\u4e00-\u9fa5\uff1f]+|[^\x00-\xff]+)"
FORMAT_RE = u"?\.(?P<format>[a-z0-9]+)"

MTCH_STAR = '^'
MTCH_END = '$'
TRAILING_SLASH = '/'

import re
REL_RE = re.compile(r"{(resource_name)\}")

Router = namedtuple('Router', ['url_regex_tpl', 'mapping', 'name_tpl', 'init_kwargs'])
NestedRouter = namedtuple('NestedRouter', ['url_regex_tpl', 'mapping', 'name_tpl', 'init_kwargs'])
DyDetailRouter = namedtuple('DyDetailRouter', ['url_regex_tpl', 'name_tpl', 'init_kwargs'])
DyListRouter = namedtuple('DyListRouter', ['url_regex_tpl', 'name_tpl', 'init_kwargs'])

class SimpleDynamicQueryRouter(SimpleRouter):

    logger = LoggerAdaptor("SimpleDynamicQueryRouter", _logger)
    _attached = []

    routers = [
        Router(#list
            url_regex_tpl='{prefix}/',
            mapping = {
                'get': 'get_{verbose_key}s',
            },
            name_tpl = '{prefix_abbr}_{verbose_key}(s)', # 'wct_accounts', must be in plural form
            init_kwargs = {}
        ),
        Router(
            url_regex_tpl='{prefix}/{look_at}/',
            mapping = {
                'get': 'get_{verbose_key}_by_{query_key}',
                'post': 'create_{verbose_key}_by_{query_key}',
                'put': 'update_{verbose_key}_by_{query_key}',
                'patch': 'update_partially_{verbose_key}_by_{query_key}',
                'delete': 'delete_{verbose_key}_by_{query_key}',
            },
            name_tpl = '{prefix_abbr}_{verbose_key}',
            init_kwargs = {}
        ),
        Router(#list
            url_regex_tpl='{prefix}/resources/',
            mapping = {
                'get': 'get_resources',
            },
            name_tpl = '{prefix_abbr}_resource(s)',
            init_kwargs = {}
        ),
        NestedRouter(#list
            url_regex_tpl='{prefix}/{resource_name}/',
            mapping = {
                'get': 'get_{resource_name}s_within_{prefix}', # plural = True
            },
            name_tpl='{prefix_abbr}_{resource_name}_by_name',
            init_kwargs={}
        ),
        NestedRouter(#detailed->list
            url_regex_tpl='{prefix}/{look_at}/resources/',
            mapping = {
                'get': 'get_resources_from_{verbose_key}', # plural = True
            },
            name_tpl='{prefix_abbr}_resource(s)_from_{verbose_key}',
            init_kwargs={}
        ),
        NestedRouter(
            url_regex_tpl='{prefix}/{look_at}/{resource_name}/',
            mapping = {
                'get': 'get_{resource_name}_from_{verbose_key}',
                'post': 'create_{resource_name}_from_{verbose_key}',
                'put': 'update_{resource_name}_from_{verbose_key}',
                'patch': 'update_partially_{resource_name}_from_{verbose_key}',
                'delete': 'delete_{resource_name}_from_{verbose_key}',
            },
            name_tpl='{prefix_abbr}_{resource_name}_from_{verbose_key}',
            init_kwargs={}
        ),
        DyDetailRouter(
            url_regex_tpl='{prefix}/{look_at}/',
            name_tpl = '{method}-detail',
            init_kwargs={}
        ),
        DyListRouter(
            url_regex_tpl='{prefix}/',
            name_tpl = '{method}-list',
            init_kwargs={}
        )

    ]

    def __init__(self, is_method_attached=True, resource_name=None):
        self.is_method_attached = is_method_attached
        self._resource_name = resource_name
        self._attached = []
        self.clear()
        super(SimpleRouter, self).__init__()

    def clear(self):
        self._verbose_key = None
        self._query_key = None
        self._prefix_abbr = None
        self._resource_name = None

    def register(self, prefix, viewset, base_name=None):
        if base_name != None:
            self._prefix_abbr = base_name
        super(SimpleDynamicQueryRouter, self).register(prefix, viewset, base_name)

    def get_attr(self, nested_view_router, attr_name, default=None):
        attr = getattr(nested_view_router, attr_name, default)
        # if not attr:
        #     raise KeyError("{0} Not Defined!".format(attr_name))
        return attr

    def get_method_map(self, nested_view_router, method_map, **kwargs):
        bounded_method = {}

        for http_action, methodname_tpl in method_map.items():
            methodname = methodname_tpl.format(**kwargs).lower()

            if hasattr(nested_view_router, methodname) or self.is_method_attached:
                bounded_method[http_action] = methodname
        self._attached.append({nested_view_router.queryset.model._meta.object_name: bounded_method})
        # self.logger.info('router._attached: %s', self._attached)
        return bounded_method

    def get_verbose_key(self, nested_view_router):
        if not self._verbose_key:
            attr = self.get_attr(nested_view_router, 'verbose_key')
            self._verbose_key = attr
        return self._verbose_key

    def get_query_key(self, nested_view_router):
        if not self._query_key:
            attr = self.get_attr(nested_view_router, 'query_key')
            self._query_key = attr
        return self._query_key

    def get_prefix_abbr(self, nested_view_router):
        if not self._prefix_abbr:
            attr = self.get_attr(nested_view_router, 'prefix_abbr')
            self._prefix_abbr = attr
        return self._prefix_abbr

    def get_resource_name(self, nested_view_router):
        if not self._resource_name:
            # self._resource_name = "resource"
            attr = self.get_attr(nested_view_router, 'affiliates', None)
            self._resource_name = attr
        return self._resource_name

    def get_look_at_regex(self, nested_view_router, look_at_prefix=''):
        """
       ' Given a viewset, return the portion of URL regex that is used
        to match against a single instance.

        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.

        https://github.com/alanjds/drf-nested-routers ' quoted by django_rest
        """
        query_key = self.get_attr(nested_view_router, 'query_key', 'pk')
        look_at_regex = QUERY_KEY_RE.format(look_at_prefix=look_at_prefix, query_key=query_key)
        return look_at_regex


    def get_routers(self, nested_view_router, **kwargs):

        # known actions
        known_actions = flatten([route.mapping.values() for route in self.routes
                                 if isinstance(route, Router)])
        # get methods attached to the view
        detail_router, list_router = [], []
        # if @detail @list decorate the method, we reserve it for updating
        for methodname in dir(nested_view_router):
            attr = self.get_attr(nested_view_router, methodname)
            http_methods = getattr(attr, "binding_to_methods", None)
            detail = getattr(attr, 'detail', True)
            if http_methods:
                # user are using decorator to bind methods
                # we need to modify these codes
                if methodname in known_actions:
                    raise ImproperlyConfigured('method {0} has already been in router method mapping')
                if detail:
                    detail_router.append(({http_action:methodname for http_action in http_methods}, methodname))
                else:
                    list_router.append(({http_action:methodname for http_action in http_methods}, methodname))

        def _get_query_router(router):
            return [Router(
                url_regex_tpl = router.url_regex_tpl,
                mapping=router.mapping,
                name_tpl=router.name_tpl,
                init_kwargs=router.init_kwargs
            )]

        def _get_detail_router(router, detail_ret):

            ret = []
            for _mapping, methodname in detail_ret:

                ret.append(DyDetailRouter(
                    url_regex_tpl=router.url_regex_tpl.format(methodname=methodname),
                    mapping=router.mapping.update(_mapping),
                    name_tpl=router.name_tpl.format(method=methodname),
                    init_kwargs=router.init_kwargs)
                )
            return ret

        def _get_list_router(router, list_ret):
            ret = []
            for _mapping, methodname in list_ret:

                ret.append(DyListRouter(
                    url_regex_tpl=router.url_regex_tpl.format(methodname=methodname),
                    mapping=router.mapping.update(_mapping),
                    name_tpl=router.name_tpl.format(method=methodname),
                    init_kwargs=router.init_kwargs)
                )
            return ret

        def _compose_nested_router(router, names):
            ret = []
            if names is None:
                # do implementation here
                pass
            else:
                for name in names:
                    _map = {}

                    for k, v in router.mapping.items():
                        _map[k] = REL_RE.sub(name, v)

                    ret.append(NestedRouter(
                        url_regex_tpl=REL_RE.sub('(?P<resource_name>{name})'.format(name=name)+'/'+RESOURCE_QK_RE, router.url_regex_tpl),# !important
                        mapping=_map,
                        name_tpl=REL_RE.sub(name, router.name_tpl),
                        init_kwargs=router.init_kwargs))

            return ret

        # return routers
        ret = []

        for router in self.routers:
            # add method routing to every router

            if   isinstance(router, NestedRouter):
                ret += _compose_nested_router(router, kwargs.get('resource_name', None))
            elif isinstance(router, Router):
                ret += _get_query_router(router)
            elif isinstance(router, DyDetailRouter):
                ret += _get_detail_router(router, detail_router)
            elif isinstance(router, DyListRouter):
                ret += _get_list_router(router, list_router)
        # self.logger.info('ret: %s', ret)
        return ret

    def get_urls(self):

        ret = []
        for prefix, nested_view_router, \
            basename in self.registry:
            self.clear()
            # get 'look_at' regex, verbose_key, prefix_abbr
            look_at = self.get_look_at_regex(nested_view_router)
            verbose_key = self.get_verbose_key(nested_view_router)
            query_key = self.get_query_key(nested_view_router)
            prefix_abbr = self.get_prefix_abbr(nested_view_router) or basename
            resource_name = self.get_resource_name(nested_view_router)
            # get routers related to the nested_view_router
            _routers = self.get_routers(nested_view_router, resource_name=resource_name)
            # loop through routers and compose url

            for router in _routers:
                # get method mapping
                # self.logger.info('router: %s', str(type(router)))
                if isinstance(router, Router):
                    method_mapping = self.get_method_map(nested_view_router, router.mapping,
                                                         verbose_key=verbose_key, query_key=query_key, prefix=prefix)
                if isinstance(router, NestedRouter):
                    method_mapping = self.get_method_map(nested_view_router, router.mapping,
                                                         verbose_key=verbose_key, query_key=query_key, prefix=prefix, resource_name=resource_name)
                # form url regex
                url_regex = self.compose_url_regex(router.url_regex_tpl, look_at, prefix, RESOURCE_NAME_RE)
                # form name
                name = self.compose_name(router.name_tpl, prefix_abbr, verbose_key, resource_name)
                # produce view function
                try:
                    view_func = nested_view_router.as_view(method_mapping, **router.init_kwargs) # ?
                except TypeError as err:
                    self.logger.info(err)
                    self.logger.info('method_mapping: %s', method_mapping)
                    import traceback
                    traceback.print_exc()
                # append to url list
                ret.append(url(url_regex, view_func, name=name))

        return ret


    def compose_url_regex(self, url_regex_tpl, look_at, prefix, resource_name_re):
        # self.logger.info("look_at: %s", look_at)
        url_regex = \
            url_regex_tpl.format(prefix=prefix, look_at=look_at, resource_name=resource_name_re) + \
            MTCH_END
        return url_regex

    def compose_name(self, name_tpl, prefix_abbr, verbose_key, resource_name_re):
        name = name_tpl.format(prefix_abbr=prefix_abbr, verbose_key=verbose_key, resource_name=resource_name_re)
        return name

class RelationalDynamicQueryRouter(SimpleDynamicQueryRouter):

    logger = LoggerAdaptor("RelationalDynamicQueryRouter", _logger)

    def _process_view(self, viewset, methodname, query_key, prefix):
        if   methodname.upper() == 'GET':
            self._process_get_view(self, viewset, methodname, query_key, prefix)
        elif methodname.upper() == 'POST':
            self._process_create_view(self, viewset, methodname, query_key, prefix)
        elif methodname.upper() == 'PUT':

            self._process_update_view(self, viewset, methodname, query_key, prefix)
        elif methodname.upper() == 'PATCH':
            self._proces_partially_update(self, viewset, methodname, query_key, prefix)
        elif methodname.upper() == 'DELETE':
            self._process_delete_view(self, viewset, methodname, query_key, prefix)

    def _process_delete_view(self, viewset, methodname, query_key, prefix):

        __code = """
def {method_name}(self, req,
                        {query_key}=None,
                        **kwargs):
        raise Exception("Not Implemented: {method_name}")

_gen_func_hook = {method_name}
setattr(viewset, '{method_name}', _gen_func_hook)
        """
        viewset._logger = self.logger
        __code = __code.format(method_name=methodname, query_key=query_key)
        self.logger.info('_code_gen of %s: %s', viewset.__name__ , __code)
        try:
            exec(__code)
        except Exception as err:
            raise(err)


    def _process_create_view(self, viewset, methodname, query_key, prefix):

        __code = """
def {method_name}(self, req,
                        {query_key}=None,
                        resource_name=None,
                        res_query_key=None,
                        **kwargs):
        raise Exception("Not Implemented: {method_name}")

_gen_func_hook = {method_name}
setattr(viewset, '{method_name}', _gen_func_hook)
        """
        viewset._logger = self.logger
        __code = __code.format(method_name=methodname, query_key=query_key)
        self.logger.info('_code_gen of %s: %s', viewset.__name__ , __code)
        try:
            exec(__code)
        except Exception as err:
            raise(err)


    def _process_update_view(self, viewset, methodname, query_key, prefix):

        __code = """
def {method_name}(self, req,
                        {query_key}=None,
                        resource_name=None,
                        res_query_key=None,
                        **kwargs):
        raise Exception("Not Implemented: {method_name}")

_gen_func_hook = {method_name}
setattr(viewset, '{method_name}', _gen_func_hook)
        """
        viewset._logger = self.logger
        __code = __code.format(method_name=methodname, query_key=query_key)
        self.logger.info('_code_gen of %s: %s', viewset.__name__ , __code)
        try:
            exec(__code)
        except Exception as err:
            raise(err)


    def _proces_partially_update(self, viewset, methodname, query_key, prefix):

        __code = """
def {method_name}(self, req,
                        {query_key}=None,
                        resource_name=None,
                        res_query_key=None,
                        **kwargs):
        raise Exception("Not Implemented: {method_name}")

_gen_func_hook = {method_name}
setattr(viewset, '{method_name}', _gen_func_hook)
        """
        viewset._logger = self.logger
        __code = __code.format(method_name=methodname, query_key=query_key)
        self.logger.info('_code_gen of %s: %s', viewset.__name__ , __code)
        try:
            exec(__code)
        except Exception as err:
            raise(err)


    def _process_get_view(self, viewset, methodname, query_key, prefix):

        __code = """
def {method_name}(self, req,
                        {query_key}=None,
                        resource_name=None,
                        res_query_key=None,
                        **kwargs):

       def to_url_param(kwargs):
            args_proc = lambda o: u'='.join([o[0],o[1]])
            ob_map = map(args_proc, list(kwargs.items()))
            return list(ob_map)
       try:

            url_args = [u'{{ref}}={{val}}', ]
            url_args.extend(to_url_param(kwargs))
            # self.logger.info(u"new_kwargs: %s", kwargs)
            # self.logger.info(u"url_args: %s", url_args)

            from RESTful_api.urls import PREFIX
            from api.views import parse

            WSGI_Req = req._request
            SCHEME = 'http://'
            HOST = WSGI_Req.META['HTTP_HOST']# protocle
            REMOTE_ADDR = WSGI_Req.META['REMOTE_ADDR']
            PROTOCOL = WSGI_Req.META['SERVER_PROTOCOL']

            RES_URL_tpl = u"{{resource_name}}/?" if not res_query_key \
                                               else '/'.join([u"{{resource_name}}", res_query_key]) + '/?'
            next_url_tpl = SCHEME + HOST + '/' + PREFIX.lstrip('^') + RES_URL_tpl  + '&'.join(url_args)
            self.logger.info(u'gen_next_url_tpl: %s', next_url_tpl)
            next_url = next_url_tpl.format(resource_name=parse(resource_name),
                                          ref='{query_key}', val={query_key})
            self.logger.info(u'gen_next_url: %s', next_url)
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(next_url)
       except Exception as err:
            import traceback
            traceback.print_exc()
            raise(err)


_gen_func_hook = {method_name}
setattr(viewset, '{method_name}', _gen_func_hook)
        """
        viewset._logger = self.logger
        __code = __code.format(method_name=methodname, query_key=query_key)
        self.logger.info('_code_gen of %s: %s', viewset.__name__ , __code)
        try:
            exec(__code)
        except Exception as err:
            raise(err)

    def get_method_map(self, nested_view_router, method_map, **kwargs):
        query_key = kwargs['query_key']
        prefix = kwargs['prefix']
        resource_name = kwargs.get('resource_name', None)
        if prefix:
            if '/' in prefix:
                v = '_'.join(prefix.split('/'))
                kwargs['prefix'] = v
        bounded_method = super(RelationalDynamicQueryRouter, self).get_method_map(nested_view_router, method_map, **kwargs)
        if not resource_name:
            return bounded_method
        if self.is_method_attached:
            for http_action, methodname in bounded_method.items():
                self._process_view(nested_view_router, methodname, query_key, prefix)
        return bounded_method


class DefaultDynamicQueryRouter(RelationalDynamicQueryRouter):#SimpleDynamicQueryRouter

    logger = LoggerAdaptor("DefaultDynamicQueryRouter", _logger)

    """
    The default router extends the SimpleRouter, but also adds in a default
    API root view, and adds format suffix patterns to the URLs.
    """
    include_root_view = True
    include_format_suffixes = True
    root_view_name = 'root'

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        for prefix, viewset, basename in self.registry:
            prefix_abbr = self.get_attr(viewset, 'prefix_abbr')
            verbose_key = self.get_attr(viewset, 'verbose_key')
            api_root_dict[prefix] = '{prefix_abbr}_{verbose_key}(s)'.format(prefix_abbr=prefix_abbr, verbose_key=verbose_key)

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = request.resolver_match.namespace
                for key, url_name in api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name
                    try:
                        ret[key] = reverse(
                            url_name,
                            args=args,
                            kwargs=kwargs,
                            request=request,
                            format=kwargs.get('format', None)
                        )
                    except NoReverseMatch:
                        # Don't bail out if eg. no list routes exist, only detail routes.
                        continue

                return Response(ret)

        return APIRoot.as_view()

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = []

        if self.include_root_view:
            root_url = url(r'^$', self.get_api_root_view(), name=self.root_view_name)
            urls.append(root_url)

        default_urls = super(DefaultDynamicQueryRouter, self).get_urls()
        urls.extend(default_urls)

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)

        # self.logger.info("router.urls: %s", json.dumps([str(item) for item in urls], sort_keys=True, indent=4))
        # self.logger.info("attached methods: %s", json.dumps(self._attached, sort_keys=True, indent=4))
        return urls