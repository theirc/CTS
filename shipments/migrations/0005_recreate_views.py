# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from shipments.db_views import add_views, drop_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0004_auto_20140916_1409'),
    ]

    operations = [
        # Forward or back, we drop the views and then add them again
        migrations.RunPython(drop_views, add_views),
        migrations.RunPython(add_views, drop_views),
    ]
