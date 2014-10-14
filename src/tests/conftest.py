from django.conf import settings

# OAuth is optional and won't work if there is no oauth_provider & oauth2
try:
    import oauth_provider
    import oauth2
except ImportError:
    pass
else:
    INSTALLED_APPS += (
        'oauth_provider',
    )

try:
    import provider
except ImportError:
    pass
else:
    INSTALLED_APPS += (
        'provider',
        'provider.oauth2',
    )

# guardian is optional
try:
    import guardian
except ImportError:
    pass
else:
    ANONYMOUS_USER_ID = -1
    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend', # default
        'guardian.backends.ObjectPermissionBackend',
    )
    INSTALLED_APPS += (
        'guardian',
    )


def pytest_configure():
    settings.configure(
        DEBUG = True,
        TEMPLATE_DEBUG = True,
        DEBUG_PROPAGATE_EXCEPTIONS = True,
        ALLOWED_HOSTS = ['*'],
        ADMINS = (),
        MANAGERS = (),
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
                'NAME': '',                     # Or path to database file if using sqlite3.
                'USER': '',                      # Not used with sqlite3.
                'PASSWORD': '',                  # Not used with sqlite3.
                'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
                'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
            }
        },
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        },
        TIME_ZONE = 'UTC',
        LANGUAGE_CODE = 'en-uk',
        SITE_ID = 1,
        USE_I18N = True,
        USE_L10N = True,
        MEDIA_ROOT = '',
        MEDIA_URL = '',
        SECRET_KEY = 'u@x-aj9(hoh#rb-^ymf#g2jx_hp0vj7u5#b@ag1n^seu9e!%cy',
        TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ),
        MIDDLEWARE_CLASSES = (
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        ROOT_URLCONF = 'testapp.urls',
        TEMPLATE_DIRS = (),
        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'rest_framework_nested',
            'testapp',
        ),
        STATIC_URL = '/static/',
        PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.SHA1PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
            'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
            'django.contrib.auth.hashers.BCryptPasswordHasher',
            'django.contrib.auth.hashers.MD5PasswordHasher',
            'django.contrib.auth.hashers.CryptPasswordHasher',
        ),
        AUTH_USER_MODEL = 'auth.User'
    )
