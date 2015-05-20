# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from shipments.db_views import drop_views, add_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0011_auto_20141023_1542'),
    ]

    operations = [
        migrations.RunPython(drop_views, add_views),
        migrations.AddField(
            model_name='package',
            name='date_in_transit',
            field=models.DateTimeField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='package',
            name='date_picked_up',
            field=models.DateTimeField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='package',
            name='date_received',
            field=models.DateTimeField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(add_views, drop_views),
    ]
