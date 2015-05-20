# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion

from shipments.db_views import drop_views, add_views


class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0015_auto_20141030_1225'),
    ]

    operations = [
        migrations.RunPython(drop_views, add_views),
        migrations.AlterField(
            model_name='package',
            name='last_scan',
            field=models.ForeignKey(related_name='last_packages', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='shipments.PackageScan', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='package',
            name='shipment',
            field=models.ForeignKey(related_name='packages', to='shipments.Shipment'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='packageitem',
            name='package',
            field=models.ForeignKey(related_name='items', to='shipments.Package'),
            preserve_default=True,
        ),
        migrations.RunPython(add_views, drop_views),
    ]
