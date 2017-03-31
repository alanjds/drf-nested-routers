__author__ = 'wangyi'

import hmac
import hashlib
import base64
from uuid import uuid4
import random
import string

from django.utils import timezone
from api.utils.datetime import to_seconds_from_datetime

def app_key_gen():
    return ''.join([random.SystemRandom().choice("{}".format(string.ascii_uppercase)) for i in range(16)])

def app_secret_coder(api_secret, msg, algorithm="hmac-sha256"):
    algo, hash_scheme = algorithm.split("-")
    if algo == "hmac" and hash_scheme == "sha256":
        digest_obj = hmac.new(api_secret, msg=msg, digestmod=hashlib.sha256).digest()
    else:
        raise Exception("(%s, %s) Not Be Supported Yet!" % (algo, hash_scheme))
    return base64.b64encode(digest_obj).decode()

def app_secret_gen():
    coder = hashlib.sha256()
    salt = uuid4().hex
    coder.update(timezone.now().strftime('%H%M%S')+salt)
    return coder.hexdigest()

def check_sign_sim(sign_req, sign_serv):
    # check algorithm
    # decide cmp algorithm and whether to update
    return sign_req == sign_serv
