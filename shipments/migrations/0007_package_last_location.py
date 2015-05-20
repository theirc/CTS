# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from  ..db_views import add_views, drop_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0006_auto_20140925_0813'),
    ]

    operations = [
        migrations.RunPython(drop_views, add_views),
        migrations.AddField(
            model_name='package',
            name='last_location',
            field=models.ForeignKey(related_name=b'last_packages', blank=True, to='shipments.Location', null=True),
            preserve_default=True,
        ),
        migrations.RunPython(add_views, drop_views),
    ]
