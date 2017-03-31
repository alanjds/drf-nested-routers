__author__ = 'wangyi'

import logging
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# desired formmat e.g:
#  [%(levelname)s] module_name.class_name %(asctime)s:

class LoggerAdaptor(logging.LoggerAdapter):

    def __init__(self, prefix, logger):
        # super(self, App_LoggerAdaptor).__init__(logger, {})
        logging.LoggerAdapter.__init__(self, logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        return "%s %s" % (self.prefix, msg), kwargs

