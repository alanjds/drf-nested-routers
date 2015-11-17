#!/usr/bin/env python
import os

from setuptools import find_packages, setup

curdir = os.path.dirname(os.path.abspath(__file__))

setup(
    name='drf-nested-routers',
    description='Nested resources for the Django Rest Framework',
    long_description=open('README.md').read(),
    license='Apache',
    version='0.11.1',
    author='Alan Justino et al.',
    author_email='alan.justino@yahoo.com.br',
    url='https://github.com/alanjds/drf-nested-routers',
    install_requires=['djangorestframework>=2.4'],
    setup_requires=['setuptools'],
    packages=find_packages(curdir),
)
