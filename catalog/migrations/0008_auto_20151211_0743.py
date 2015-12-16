# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_auto_20141106_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donor',
            name='t1_codes',
            field=models.ManyToManyField(help_text='Add a T1 Code', related_name='t1_donors', to='catalog.DonorCode', blank=True),
        ),
        migrations.AlterField(
            model_name='donor',
            name='t3_codes',
            field=models.ManyToManyField(help_text='Add a T3 Code', related_name='t3_donors', to='catalog.DonorCode', blank=True),
        ),
    ]
