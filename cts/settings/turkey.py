import os

os.environ['INSTANCE'] = 'turkey'

from cts.settings.staging import *  # noqa

# There should be only minor differences from staging

LEAFLET_CONFIG['DEFAULT_CENTER'] = (39.56, 32.52)
LEAFLET_CONFIG['DEFAULT_ZOOM'] = 6
