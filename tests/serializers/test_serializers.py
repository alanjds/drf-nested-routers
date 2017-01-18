import json
import pytest
from django.core.urlresolvers import reverse
from django.test import TestCase

from tests.serializers.models import Parent, Child1, Child2


class TestSerializers(TestCase):

    def get_json_response(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=response)
        return json.loads(response.content.decode('utf-8'))

    @classmethod
    def setUpClass(cls):
        pytest.importorskip("rest_framework", minversion="3.1.0")
        parent = Parent.objects.create(name='Parent')

        Child1.objects.create(parent=parent, name='Child1-A')
        Child1.objects.create(parent=parent, name='Child1-B')
        Child1.objects.create(parent=parent, name='Child1-C')

        Child2.objects.create(root=parent, name='Child2-A')
        Child2.objects.create(root=parent, name='Child2-B')
        Child2.objects.create(root=parent, name='Child2-C')

        Parent.objects.create(name='Parent2')
        return super(TestSerializers, cls).setUpClass()

    def test_default(self):
        url = reverse('parent1-detail', kwargs={'pk': 1})
        data = self.get_json_response(url)

        self.assertEqual(len(data['first']), 3)
        self.assertTrue('url' in data['first'][0])
        self.assertIn('/parent1/1/child1/1/', data['first'][0]['url'])
        self.assertIn('/parent1/1/child1/2/', data['first'][1]['url'])
        self.assertIn('/parent1/1/child1/3/', data['first'][2]['url'])

    def test_custom(self):
        return
        url = reverse('parent2-detail', kwargs={'pk': 1})
        data = self.get_json_response(url)

        self.assertEqual(len(data['second']), 3)
        self.assertTrue('url' in data['second'][0])
        self.assertIn('/parent2/1/child2/1/', data['second'][0]['url'])
        self.assertIn('/parent2/1/child2/2/', data['second'][1]['url'])
        self.assertIn('/parent2/1/child2/3/', data['second'][2]['url'])

    def test_no_children(self):
        return
        url = reverse('parent-detail', kwargs={'pk': 2})
        data = self.get_json_response(url)

        self.assertEqual(len(data['first']), 0)
