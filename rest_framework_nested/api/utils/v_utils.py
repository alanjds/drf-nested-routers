__author__ = 'wangyi'

import django_filters
from rest_framework import filters
from rest_framework.response import Response
MODEL_PREFIX = 'third_party.models.'
SERIALIZER_PREFIX = 'third_party.serializer'
# magic method
def get_args_by_req(req,
                    prop_args=None,
                    expected_header_args=None,
                    f=None):

    ol = None
    # header: req.META

    # req.[url_method]
    method = req.method
    try:
        _full_args = req.__getattribute__(method)
    except:
        _full_args = {}
    if prop_args is None:
        ol = _full_args
    else:
        if isinstance(prop_args, str):
            ol = {key:_full_args[key] for \
                    key in prop_args.split(',')}
        else:
            raise Exception("Not Implemented!")

    if f is not None:
        ol = f(ol)
    return ol

# help function for get_res_model
def to_kls(short_cut):
    if short_cut.lower() == 'wechat':
        return 'WeChatAccount'
    if short_cut.lower() == 'messages':
        return 'WeChatMSG'
    return short_cut

def Import_factory(*args, **kwargs):
    if kwargs == {}:
        ob_map = map(to_kls, args)
        if len(args) == 1:
            kls_path = MODEL_PREFIX + '.'.join(ob_map)
        else:
            kls_path = '.'.join(ob_map)

        from django.utils.module_loading import import_string
        try:
            kls = import_string(kls_path)
        except ImportError as err:
            raise err
        return kls.__name__, kls

    else:
        raise Exception("Not Implemented!")
    # from third_party.models import WeChatMSG
    # res_label = WeChatMSG.__name__
    # return res_label, WeChatMSG
