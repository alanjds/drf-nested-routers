__author__ = 'wangyi'

import datetime
import time
import calendar

def to_seconds_from_datetime(dt):
    return time.mktime(dt.timetuple())

def to_seconds_from_datetime2(dt):
    return calendar.timegm(dt.timetuple())