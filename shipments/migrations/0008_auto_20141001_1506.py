# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def do_nothing(apps, schemaeditor):
    pass


def update_last_locations(apps, schema_editor):
    Location = apps.get_model("shipments", "Location")
    last_locations = Location.objects.order_by('package__id', '-when')
    last_locations = last_locations.prefetch_related('package')
    last_locations = last_locations.distinct('package')
    for loc in last_locations:
        loc.package.last_location = loc
        loc.package.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0007_package_last_location'),
    ]

    operations = [
        migrations.RunPython(update_last_locations, do_nothing)
    ]
