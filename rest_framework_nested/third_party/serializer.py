from __future__ import unicode_literals
__author__ = 'wangyi'

from rest_framework import serializers
from models import User, WebSite, Headline, UserWebSite
import contextlib

__all__ = ['WebSiteSerializer', 'UserSerializer', 'HeadlineSerializer', 'SerializerManager']


class SerializerManager(object):

    def __init__(self, cls):
        self.cls = cls

    def __get__(self, caller, caller_type=None):
        self.owner = caller
        return self

    @contextlib.contextmanager
    def only(self):
        try:
            if hasattr(self.owner, 'cols') and self.owner.sign:
                setattr(self.cls.Meta, '__sign', self.owner.sign)
                setattr(self.cls.Meta, '__fields', self.owner.cols)
            yield
        except Exception as err:
            import traceback
            traceback.print_exc()
            raise(err)
        finally:
            if hasattr(self.cls, '_fields') and\
                    (hasattr(self.owner, 'cols') or hasattr(self.owner, 'sign')):
                del self.cls._fields

            if hasattr(self.owner, 'cols'):
                self.owner.cols = None
            if hasattr(self.owner, 'sign'):
                self.owner.sign = None

    def __call__(self, objects, **kwargs):
        # self.cls.__sign, self.cls.__fields =
        #     self.owner.sign, self.owner.cols,
        many = kwargs.pop('many', False)
        if many:
            with self.only():
                repr = self.cls(data=objects, many=True,
                                sign=self.owner.sign,
                                fields=self.owner.cols,
                                **kwargs)
                repr.is_valid()
            return repr.data
        else:
            return self.cls(objects, **kwargs).data


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __new__(cls, *args, **kwargs):
        # We override this method in order to automagically create
        # `ListSerializer` classes instead when `many=True` is set.
        sign = kwargs.pop('sign', None)
        fields = kwargs.pop('fields', None)
        if kwargs.pop('many', False):
            cls.drop_cols(sign, fields)
            return cls.many_init(*args, **kwargs)
        return super(DynamicFieldsModelSerializer, cls).__new__(cls, *args, **kwargs)

    @property
    def data(self):
        data = super(DynamicFieldsModelSerializer, self).data

        def walk_json(data, target_key):
            descendant = [data]

            try:
                while len(descendant) != 0:
                    curr = descendant.pop(0)
                    if curr.get(target_key) is not None:
                        raise StopIteration

                    for key, val in curr.items():
                        if isinstance(val, dict):
                            descendant.append(val)
            except StopIteration:
                return curr
            else:
                return None

        target = walk_json(data, 'password')
        if target is not None:
            target['password'] = "********"
        return data

    def __init__(self, *args, **kwargs):
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        self._drop_cols()

    def _drop_cols(self):
        if hasattr(self.Meta, '__sign') and \
                hasattr(self.Meta, '__fields'):
            try:
                # the following method doesn't work
                sign = self.Meta.__sign
                fields = self.Meta.__fields
            except:
                return
            if fields is not None:
                if sign \
                        == u'+':
                    allowed = set(self.__fields)
                    existing = set(self.fields.keys())
                    for field_name in existing - allowed:
                        self.fields.pop(field_name)
                elif sign \
                        == u'-':
                    for fields_name in self.__fields:
                        self.fields.pop(fields_name)

    @classmethod
    def drop_cols(cls, sign=None, fields=None):
        if fields is not None:
            allowed = set(fields)
            _cls_fields = cls().fields
            if sign == u'+':
                existing = set(_cls_fields.keys())
                for field_name in existing - allowed:
                    _cls_fields.pop(field_name)
            elif sign == u'-':
                for field_name in fields:
                    _cls_fields.pop(field_name)
            cls._fields = _cls_fields
            return \
                cls


class UserSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = User
        fields = '__all__'
        depth = 3


class WebSiteSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = WebSite
        fields = '__all__'
        depth = 3


class HeadlineSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Headline
        fields = '__all__'
        depth = 3


class UserWebsiteSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = UserWebSite
        fields = '__all__'
        depth = 3
