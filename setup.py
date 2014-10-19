#!/usr/bin/env python
import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test

curdir = os.path.dirname(os.path.abspath(__file__))


class TestCommand(test):
    user_options = []

    def initialize_options(self):
        test.initialize_options(self)

    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        from rest_framework_nested.runtests import runtests
        errno = runtests.main()
        sys.exit(errno)

setup(
    name='drf-nested-routers',
    description='Nested resources for the Django Rest Framework',
    long_description=open('README.md').read(),
    license='Apache',
    version='0.1.3',
    author='Alan Justino and Oscar Vilaplana',
    author_email='alan.justino@yahoo.com.br, dev@oscarvilaplana.cat',
    url='https://github.com/alanjds/drf-nested-routers',
    install_requires=['djangorestframework'],
    setup_requires=['setuptools'],
    packages=find_packages(curdir),
    tests_require=['djangorestframework<2.4', 'Django<1.7'],
    cmdclass={'test': TestCommand},
)
