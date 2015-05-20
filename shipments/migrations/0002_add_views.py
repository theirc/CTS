# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from shipments.db_views import add_views, drop_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_views, drop_views),
    ]
