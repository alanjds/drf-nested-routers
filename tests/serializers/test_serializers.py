import json
import pytest
from django.test import TestCase

from tests.serializers.models import Parent, Child1, Child2, GrandChild1

try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse


class TestSerializers(TestCase):

    def get_json_response(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, msg=response)
        response_data = response.content.decode('utf-8')
        print(response_data)
        return json.loads(response_data)

    def post_json_request(self, url, data):
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201, msg=response)
        response_data = response.content.decode('utf-8')
        print(response_data)
        return json.loads(response_data)

    @classmethod
    def setUpClass(cls):
        pytest.importorskip("rest_framework", minversion="3.1.0")
        parent = Parent.objects.create(name='Parent')

        Child1.objects.create(parent=parent, name='Child1-A')
        Child1.objects.create(parent=parent, name='Child1-B')
        Child1.objects.create(parent=parent, name='Child1-C')

        child2 = Child2.objects.create(root=parent, name='Child2-A')
        Child2.objects.create(root=parent, name='Child2-B')
        Child2.objects.create(root=parent, name='Child2-C')

        GrandChild1.objects.create(parent=child2, name='Child2-GrandChild1-A')
        GrandChild1.objects.create(parent=child2, name='Child2-GrandChild1-B')
        GrandChild1.objects.create(parent=child2, name='Child2-GrandChild1-C')

        Parent.objects.create(name='Parent2')
        return super().setUpClass()

    def test_default(self):
        url = reverse('parent1-detail', kwargs={'pk': 1})
        data = self.get_json_response(url)

        self.assertEqual(len(data['first']), 3)
        self.assertTrue('url' in data['first'][0])
        self.assertIn('/parent1/1/child1/1/', data['first'][0]['url'])
        self.assertIn('/parent1/1/child1/2/', data['first'][1]['url'])
        self.assertIn('/parent1/1/child1/3/', data['first'][2]['url'])

    def test_multi_level(self):
        url = reverse('parent2-detail', kwargs={'pk': 1})
        data = self.get_json_response(url)

        self.assertEqual(len(data['second'][0]['grand']), 3)
        self.assertEqual(len(data['second'][1]['grand']), 0)
        self.assertEqual(len(data['second'][2]['grand']), 0)
        self.assertIn('/parent2/1/child2/1/grandchild1/1/', data['second'][0]['grand'][0]['url'])
        self.assertIn('/parent2/1/child2/1/grandchild1/2/', data['second'][0]['grand'][1]['url'])
        self.assertIn('/parent2/1/child2/1/grandchild1/3/', data['second'][0]['grand'][2]['url'])

    def test_multi_level_parent_ref(self):
        url = reverse('grandchild1-detail', kwargs={'root_pk': 1, 'parent_pk': 2, 'pk': 1})
        data = self.get_json_response(url)
        self.assertIn('/parent2/1/child2/1/', data['parent'])

    def test_multi_level_parent_ref_reverse(self):
        url = reverse('grandchild1-list', kwargs={'root_pk': 1, 'parent_pk': 2})
        data = self.post_json_request(url, {
            'name': 'NewChild',
            'parent': reverse('child2-detail', kwargs={'root_pk': 1, 'pk': 2})
        })
        self.assertEqual(data['name'], 'NewChild')

    def test_custom(self):
        url = reverse('parent2-detail', kwargs={'pk': 1})
        data = self.get_json_response(url)

        self.assertEqual(len(data['second']), 3)
        self.assertTrue('url' in data['second'][0])
        self.assertIn('/parent2/1/child2/1/', data['second'][0]['url'])
        self.assertIn('/parent2/1/child2/2/', data['second'][1]['url'])
        self.assertIn('/parent2/1/child2/3/', data['second'][2]['url'])

    def test_no_children(self):
        url = reverse('parent1-detail', kwargs={'pk': 2})
        data = self.get_json_response(url)

        self.assertEqual(len(data['first']), 0)
