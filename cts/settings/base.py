# Django settings for cts project.
import os

from datetime import timedelta

# ENVIRONMENT can be 'staging', 'production'
ENVIRONMENT = os.environ['ENVIRONMENT']
# INSTANCE might be 'jordan', 'turkey', etc.
INSTANCE = os.environ['INSTANCE']
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
    ('Caktus CTS Team', 'irc-team@caktusgroup.com'),
)
# "FROM" address
SERVER_EMAIL = 'irc-team@caktusgroup.com'
DEFAULT_FROM_EMAIL = SERVER_EMAIL

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'cts',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'public', 'media')

# Will expect all URLs to have this prefix
# Should either be empty, or be a string starting with '/' but not ending
# with '/', so that we can unconditionally put it in front of most URLs
# and end up with a valid URL.
# Need to manually put this on the front of MEDIA_URL and the end of
# LOGIN_REDIRECT_URL in a more specific settings file, unfortunately.
PREFIX_URL = os.environ.get('PREFIX_URL', '')
assert len(PREFIX_URL) == 0 or (PREFIX_URL.startswith('/') and not PREFIX_URL.endswith('/'))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = PREFIX_URL + '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'public', 'static')
PROTECTED_ROOT = os.path.join(STATIC_ROOT, 'protected')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
# (STATIC_URL does NOT change with PREFIX_URL, because the static files
# are served from a single tree by Nginx, not Django.)
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ.get('SECRET_KEY', 'qr7rsp_z@z5_=*)n6^a6e^(83=ctdz_1!_zilo%u=uu^(qgabj')

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'currency.context_processors.currencies',
    'cts.utils.context_processor',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'session_security.middleware.SessionSecurityMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'cts.prefixed_urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'cts.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

FIXTURE_DIRS = (
    os.path.join(BASE_DIR, 'fixtures'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    # External apps
    'compressor',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'selectable',
    'session_security',
    'leaflet',
    'django_hstore',
    'rest_framework_swagger',
    'djcelery',  # for 'django-admin.py celery [worker|beat]' commands
    'django_tables2',
    'django_tables2_reports',
    'bootstrap3',
    'django_extensions',
    # Project apps
    'catalog',
    'shipments',
    'accounts',
    'currency',
    'reports',
    'ona',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Application settings

AUTH_USER_MODEL = 'accounts.CtsUser'

#  session-security
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SECURITY_WARN_AFTER = 29 * 60
SESSION_SECURITY_EXPIRE_AFTER = 30 * 60

LOGIN_URL = 'account_login'
LOGOUT_URL = 'account_logout'
LOGIN_REDIRECT_URL = PREFIX_URL + '/'

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
)

# The second currency for this instance
LOCAL_CURRENCY = 'JOD'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # We use token-based auth for the actual API
        'rest_framework.authentication.TokenAuthentication',
        # But it's convenient to browse the API via http too,
        # using Django session auth
        'rest_framework.authentication.SessionAuthentication',
    ),

    'DEFAULT_FILTER_BACKENDS': ['rest_framework.filters.DjangoFilterBackend'],

    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    'PAGINATE_BY': 50,                 # Default to 50
    'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
    # 'MAX_PAGINATE_BY': 500,             # Maximum limit allowed when using `?page_size=xxx`.
}


LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (34.81, 39.04),
    'DEFAULT_ZOOM': 8,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 15,
    'RESET_VIEW': False,
    'PLUGINS': {
        'cluster': {
            'css': [
                'lib/Leaflet.markercluster/MarkerCluster.Default.css',
                'lib/Leaflet.markercluster/MarkerCluster.css'
            ],
            'js': 'lib/Leaflet.markercluster/leaflet.markercluster.js',
            'auto-include': True,
        },
    },
    'TILES': [
        ('ESRI', 'http://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', ''),  # noqa
        ('OSM', 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', ''),
    ]
}

WORLD_BORDERS_SHAPEFILE = os.path.join(
    PROJECT_ROOT, 'shipments', 'data', 'TM_WORLD_BORDERS_SIMPL-0.3.shp'
)

# We set `expires` so that if the queue gets hung or the workers go down,
# tasks don't pile up in the queue leading to a thundering herd problem
# when things start running again.
CELERYBEAT_SCHEDULE = {
    'process_new_scans': {
        'task': 'ona.tasks.process_new_scans',
        'schedule': timedelta(minutes=15),
        'expires': 10*60,  # 10 minutes
    },
    'verify_deviceid': {
        'task': 'ona.tasks.verify_deviceid',
        'schedule': timedelta(minutes=60),
        'expires': 50*50,  # 50 minutes
    },
}
CELERY_RESULT_BACKEND = None  # We never care about task results

# See https://github.com/johnsensible/django-sendfile
SENDFILE_URL = "/protected/"
SENDFILE_BACKEND = 'sendfile.backends.development'

BOOTSTRAP3 = {
    'success_css_class': '',
}
