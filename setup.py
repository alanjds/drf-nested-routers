#!/usr/bin/env python
import os

from setuptools import find_packages, setup

curdir = os.path.dirname(os.path.abspath(__file__))

setup(
    name='rest_framework_nested',
    description='Nested resources for the Django Rest Framework',
    license='Apache',
    version='0.1.0',
    author='Alan Justino and Oscar Vilaplana',
    author_email='alan.justino@yahoo.com.br, dev@oscarvilaplana.cat',
    url='https://github.com/alanjds/drf-nested-routers',
    install_requires=['djangorestframework'],
    setup_requires=['setuptools']
    packages=find_packages(curdir),
)
