# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donorcategorydata',
            name='first_date_shipped',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='donorcategorydata',
            name='last_date_shipped',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
