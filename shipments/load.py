from django.conf import settings
from django.contrib.gis.utils import LayerMapping

from shipments.models import WorldBorder

SHAPEFILE = settings.WORLD_BORDERS_SHAPEFILE


world_mapping = {
    'fips': 'FIPS',
    'iso2': 'ISO2',
    'iso3': 'ISO3',
    'un': 'UN',
    'name': 'NAME',
    'area': 'AREA',
    'pop2005': 'POP2005',
    'region': 'REGION',
    'subregion': 'SUBREGION',
    'lon': 'LON',
    'lat': 'LAT',
    'mpoly': 'MULTIPOLYGON',
}


def run(verbose=True):
    lm = LayerMapping(WorldBorder, SHAPEFILE, world_mapping,
                      transform=False, encoding='iso-8859-1')

    lm.save(strict=True, verbose=verbose)
