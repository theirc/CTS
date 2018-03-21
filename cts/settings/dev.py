import os
import sys

os.environ['ENVIRONMENT'] = 'dev'
os.environ['INSTANCE'] = 'local'
os.environ['PREFIX_URL'] = ''

from cts.settings.base import *  # noqa

INSTANCE_NAME = 'Local'
INSTANCES = [
    # Name, prefix
    (INSTANCE_NAME, ''),
]

PUBLIC_ROOT = os.path.join(PROJECT_ROOT, 'public')

DEBUG = True

INTERNAL_IPS = ('127.0.0.1', )

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SOUTH_TESTS_MIGRATE = True

CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

COMPRESS_ENABLED = False

# See https://github.com/johnsensible/django-sendfile
SENDFILE_ROOT = os.path.join(PUBLIC_ROOT, 'static/protected')

# Special test settings
if 'test' in sys.argv:
    COMPRESS_PRECOMPILERS = ()

    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.SHA1PasswordHasher',
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )
else:
    INSTALLED_APPS += (
        'debug_toolbar',
    )
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
