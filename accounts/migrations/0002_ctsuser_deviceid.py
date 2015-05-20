# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ctsuser',
            name='deviceid',
            field=models.CharField(default='', max_length=128, blank=True),
            preserve_default=True,
        ),
    ]
