#!/usr/bin/env python
import os

from setuptools import find_packages, setup


setup(
    name='drf-nested-routers',
    description='Nested resources for the Django Rest Framework',
    long_description=open('README.rst').read(),
    license='Apache',
    version='0.1.3.dev0',
    author='Alan Justino and Oscar Vilaplana',
    author_email='alan.justino@yahoo.com.br, dev@oscarvilaplana.cat',
    url='https://github.com/alanjds/drf-nested-routers',
    install_requires=['djangorestframework>=2.0.0, < 2.5.0'],
    packages=find_packages('src', exclude=('tests',)),
    package_dir={'': 'src'},
)
