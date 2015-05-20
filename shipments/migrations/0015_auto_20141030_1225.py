# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0014_rename_location_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packagescan',
            name='package',
            field=models.ForeignKey(related_name='scans', to='shipments.Package'),
            preserve_default=True,
        ),
    ]
