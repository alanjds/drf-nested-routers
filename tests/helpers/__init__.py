
def get_regex_pattern(urlpattern):
    if hasattr(urlpattern, 'pattern'):
        # Django 2.0
        return urlpattern.pattern.regex.pattern
    # Django < 2.0
    return urlpattern.regex.pattern