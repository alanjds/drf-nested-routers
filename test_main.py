#!/usr/bin/env python
__author__ = 'wangyi'
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rest_framework_nested.runtests.settings")
    sys.argv = ['test', 'test', 'rest_framework_nested.api.tests']
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)