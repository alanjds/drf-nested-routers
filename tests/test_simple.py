from django.test import TestCase


class TestSimple(TestCase):
    def test_one_plus_one(self):
        assert 1 + 1 == 2
