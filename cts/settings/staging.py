import os

import yaml

#                   (top)         cts           settings     staging.py
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
project_sls_file = '/srv/pillar/project.sls'
project = yaml.safe_load(open(project_sls_file, 'r'))

from cts.settings.base import *  # noqa

# Instance: 'iraq', 'jordan', 'turkey', etc.; default to whatever is first in the config
INSTANCE = os.environ.get('INSTANCE', project['instances'].keys()[0])
PREFIX_URL = project['instances'][INSTANCE]['prefix']
assert len(PREFIX_URL) == 0 or (PREFIX_URL.startswith('/') and not PREFIX_URL.endswith('/'))
LOCAL_CURRENCY = project['instances'][INSTANCE]['currency']
INSTANCE_NAME = project['instances'][INSTANCE]['name']
if PREFIX_URL:
    INSTANCE_SUFFIX = '_%s' % PREFIX_URL[1:]  # e.g. "_IQ"
else:
    INSTANCE_SUFFIX = ''

INSTANCES = [
    (project['instances'][name]['name'], project['instances'][name]['prefix'])
    for name in sorted(project['instances'].keys())
]

os.environ.setdefault('CACHE_HOST', '127.0.0.1:11211')
os.environ.setdefault('BROKER_HOST', '127.0.0.1:5672')

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# If these lines change, change conf/salt/project/db/init_sls
DATABASES['default']['NAME'] = os.environ.get('DB_NAME', 'cts_%s' % INSTANCE)
DATABASES['default']['USER'] = os.environ.get('DB_USER', 'cts_%s' % INSTANCE)

DATABASES['default']['HOST'] = os.environ.get('DB_HOST', '')
DATABASES['default']['PORT'] = os.environ.get('DB_PORT', '')
DATABASES['default']['PASSWORD'] = os.environ['DB_PASSWORD']

PUBLIC_ROOT = '/var/www/cts/public/'

STATIC_ROOT = os.path.join(PUBLIC_ROOT, 'static')
PROTECTED_ROOT = os.path.join(STATIC_ROOT, 'protected')

MEDIA_ROOT = os.path.join(PUBLIC_ROOT, 'media')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '%(CACHE_HOST)s' % os.environ,
        'KEY_PREFIX': INSTANCE,
    }
}

MEDIA_URL = PREFIX_URL + '/media/'
LOGIN_REDIRECT_URL = PREFIX_URL + '/'

# E.g. "[CTS production turkey]"
EMAIL_SUBJECT_PREFIX = '[CTS %s %s] ' % (ENVIRONMENT, INSTANCE)

COMPRESS_ENABLED = True

SESSION_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(';') + ['django-dbbackup', ]

# Uncomment if using celery worker configuration
# Each instance has its own data, so needs its own broker user/queues etc.
BROKER_URL = 'amqp://cts_%(INSTANCE)s:%(BROKER_PASSWORD)s@%(BROKER_HOST)s/cts_%(INSTANCE)s' \
             % os.environ

LOG_DIR = os.path.join(os.path.dirname(PROJECT_ROOT), 'log', INSTANCE)

# ONA related settings
ONA_DOMAIN = os.environ.get('ONA_DOMAIN%s' % INSTANCE_SUFFIX, 'ona.io')
ONA_API_ACCESS_TOKEN = os.environ.get('ONA_API_ACCESS_TOKEN%s' % INSTANCE_SUFFIX, '')
ONA_PACKAGE_FORM_IDS = os.environ.get('ONA_PACKAGE_FORM_IDS%s' % INSTANCE_SUFFIX, '11983').split(';')  # noqa
ONA_DEVICEID_VERIFICATION_FORM_ID = \
    os.environ.get('ONA_DEVICEID_VERIFICATION_FORM_ID%s' % INSTANCE_SUFFIX, '0')

# See https://github.com/johnsensible/django-sendfile
SENDFILE_ROOT = PROTECTED_ROOT
SENDFILE_URL = "/protected/"
SENDFILE_BACKEND = 'sendfile.backends.nginx'


CELERYBEAT_SCHEDULE['process_new_package_scans']['schedule'] = timedelta(minutes=2)
CELERYBEAT_SCHEDULE['verify_deviceid']['schedule'] = timedelta(minutes=2)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'basic': {
            'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'syslog': {
            'level': 'INFO',
            'class': 'logging.handlers.SysLogHandler',
            'filters': ['require_debug_false'],
            'address': '/dev/log',
            'facility': 'local6',
        }
    },
    'root': {
        'handlers': ['syslog'],
        'level': 'INFO',
    },
    'loggers': {
        # These 2 loggers must be specified, otherwise they get disabled
        # because they are specified by django's DEFAULT_LOGGING and then
        # disabled by our 'disable_existing_loggers' setting above.
        ##########################
        # BEGIN required loggers #
        ##########################
        'django': {
            'handlers': [],  # Let them propagate to root
            'level': 'ERROR',
            'propagate': True,
        },
        'py.warnings': {
            'handlers': [],
            'propagate': True,
        },
        ########################
        # END required loggers #
        ########################
        'ona': {
            'handlers': ['syslog'],
            'level': 'INFO',
            'propagate': True,
        },
        'ona.tasks': {
            'handlers': ['syslog'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

# only send emails to dpoirier (for now)
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
    # ('Caktus CTS Team', 'irc-team@caktusgroup.com'),
    ('Dan Poirier', 'dpoirier@caktusgroup.com'),
)

if 'DBBACKUP_S3_ACCESS_KEY' in os.environ:
    # backup settings

    INSTALLED_APPS += (
        'dbbackup',
    )
    DBBACKUP_S3_BUCKET = os.environ['DBBACKUP_S3_BUCKET']
    DBBACKUP_S3_ACCESS_KEY = os.environ['DBBACKUP_S3_ACCESS_KEY']
    DBBACKUP_S3_SECRET_KEY = os.environ['DBBACKUP_S3_SECRET_KEY']
    DBBACKUP_GPG_RECIPIENT = os.environ['DBBACKUP_GPG_RECIPIENT']
    DBBACKUP_GPG_ALWAYS_TRUST = os.environ['DBBACKUP_GPG_ALWAYS_TRUST'].lower() == 'true'

    DBBACKUP_SERVER_NAME = '%s-%s' % (ENVIRONMENT, INSTANCE)
    DBBACKUP_STORAGE = 'dbbackup.storage.s3_storage'
    DBBACKUP_S3_DIRECTORY = '%s/%s' % (ENVIRONMENT, INSTANCE)  # Put under production/jordan/
    os.environ.setdefault('GNUPGHOME', os.path.dirname(PROJECT_ROOT))

    # Build the backup command based on our DB settings (dbbackup is STUPID!)
    # so we can use the binary format, which is much easier to deal with on
    # restore.
    command = ['pg_dump', '--format=custom']
    db = DATABASES['default']
    if db.get('USER', False):
        command.append('--username={adminuser}')
    if db.get('HOST', False):
        command.append('--host={host}')
    if db.get('PORT', False):
        command.append('--port={port}')
    command.append('{databasename}')
    command.append('>')
    DBBACKUP_POSTGRESQL_BACKUP_COMMANDS = [command]
    del command
    del db
