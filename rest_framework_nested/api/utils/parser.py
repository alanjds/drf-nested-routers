__author__ = 'wangyi'

import re
IDENTIFIER = r"[\w][\w\d_]*"
WHITE_CHARACTER = r"[ \n\t]"
# FIELDS = r"^(\+|-)?\((?P<fields>{ID}(?:,{WHITE}*{ID})*)\)".format(ID=IDENTIFIER, WHITE=WHITE_CHARACTER)
FIELDS = r"(?P<fields>{ID}(?:,{WHITE}*{ID})*)".format(ID=IDENTIFIER, WHITE=WHITE_CHARACTER)
FIELDS_LIMIT_RE = re.compile(FIELDS)
FIELDS_SIGN = r"(\+|-)?"
FIELDS_SIGN_RE = re.compile(r"^(\+|-)?")
FIELDS_OPEN_BRACKET_RE = re.compile(r"\(")
FIELDS_CLOSE_BRACKET_RE = re.compile(r"\)")
FIELDS_ARRAY = r"(?P<fields>{SIGN}{ID}(?:,{WHITE}*{SIGN}{ID})*)".format(SIGN=FIELDS_SIGN, ID=IDENTIFIER, WHITE=WHITE_CHARACTER)
FIELDS_ARRAY_RE = re.compile(FIELDS_ARRAY)

# This function updated on 7th Nov 2016
ret_array = None
sign = None

def filed_parse(fields_string):
    sign = '+'
    ret_array = {'+':[], '-':[]}

    mtch = FIELDS_SIGN_RE.match(fields_string)
    if mtch.group() is not '' and \
                    mtch.group() in (u'+', u'-'):
        sign = mtch.group()
    _, end = mtch.span()
    mtched, new_string = _open_bracket(fields_string[end:])
    return sign, ret_array[sign]

def _open_bracket(raw_string):
    mtch = FIELDS_OPEN_BRACKET_RE.match(raw_string)
    if not mtch:
        mtched, new_string = _array_figure(raw_string)
        if new_string != '':
            raise Exception("Fields in wrong format!")
        array = mtched.split(',')
        ret_array[sign].append((sign, array[0].strip()))
        for i in array[1:]:
            i = i.strip()
            ret_array[i[0]].append(i[1:])
    else:
        _, end = mtch.span()
        mtched, new_string = _group_figure(raw_string[end:])
        _, next_new_string = _close_bracket(new_string)
        if next_new_string != '':
            raise Exception("Fields in wrong format")
        array = mtched.split(',')
        for i in array:
            ret_array[sign].append(i)

    return mtched, ''

def _close_bracket(raw_string):
    mtch = FIELDS_CLOSE_BRACKET_RE.match(raw_string)
    if not mtch:
        raise Exception("Fields not properly closed!")
    _, end = mtch.span()
    return mtch.group(), raw_string[end:]

def _group_figure(raw_string):
    mtch = FIELDS_LIMIT_RE.match(raw_string)
    if mtch is None:
        raise Exception("Fields could not be None!")
    _, end = mtch.span()
    return mtch.group(), raw_string[end:]

def _array_figure(raw_string):
    mtch = FIELDS_ARRAY_RE.match(raw_string)
    if mtch is None:
        raise Exception("Fields could not be None!")
    _, end = mtch.span()
    return mtch.group(), raw_string[end:]

if __name__ == "__main__":
    fields = "+(1,2,3,45)"
    print(filed_parse(fields))


