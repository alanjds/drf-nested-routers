__author__ = 'wangyi'

from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework.response import Response

def sys_exc_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    # Now add the HTTP status code to the response.
    if response is not None:
        pass

    return response

def handle_exc(ref, status_code, details=None):
    cause = {'Cause': "<'%s'> Does Not Exist!" % ref, 'details':details}
    rep = Response(data=cause, status=status_code)
    return rep


class REST_APIException(APIException):

    default_details = ""

    def __init__(self, detail=None):
        if detail is None:
            self.detail = self.default_details
        else:
            self.detail = {'msg':detail, 'default':self.default_details}

class REST_API_INPUT_Excepiton(REST_APIException):pass
class Cols_Not_Found(REST_API_INPUT_Excepiton):

    status_code = 5001
    default_details = "Cols Not Matched"

class BAD_SIGN(REST_API_INPUT_Excepiton):

    status_code = 5002
    default_details = "Sign Is Bad!"
