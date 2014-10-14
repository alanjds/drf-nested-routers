#!/usr/bin/env python
import os

from setuptools import find_packages, setup


setup(
    name='rest-framework-nested',
    description='Nested resources for the Django Rest Framework',
    long_description=open('README.rst').read(),
    license='Apache',
    version='0.1.0',
    author='Alan Justino and Oscar Vilaplana',
    author_email='alan.justino@yahoo.com.br, dev@oscarvilaplana.cat',
    url='https://github.com/graingert/rest-framework-nested',
    install_requires=['djangorestframework>=2.0.0, < 2.5.0'],
    packages=find_packages(),
)
