from rest_framework.views import APIView


# test strings snatched from http://www.columbia.edu/~fdc/utf8/,
# http://winrus.com/utf8-jap.htm and memory
UTF8_TEST_DOCSTRING = (
    'zażółć gęślą jaźń'
    'Sîne klâwen durh die wolken sint geslagen'
    'Τη γλώσσα μου έδωσαν ελληνική'
    'யாமறிந்த மொழிகளிலே தமிழ்மொழி'
    'На берегу пустынных волн'
    'てすと'
    'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃ'
)


class ViewWithNonASCIICharactersInDocstring(APIView):
    __doc__ = UTF8_TEST_DOCSTRING
