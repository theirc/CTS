# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_ctsuser_deviceid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ctsuser',
            name='email',
            field=models.EmailField(unique=True, max_length=250, verbose_name='email address'),
            preserve_default=True,
        ),
    ]
