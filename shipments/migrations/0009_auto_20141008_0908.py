# -*- coding: utf-8 -*-
# Views have changed; re-create them
from __future__ import unicode_literals

from django.db import models, migrations

from  ..db_views import add_views, drop_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0008_auto_20141001_1506'),
    ]

    operations = [
        # Forward or back, we drop the views and then add them again
        migrations.RunPython(drop_views, add_views),
        migrations.RunPython(add_views, drop_views),
    ]
