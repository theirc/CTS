# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20141103_1114'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ctsuser',
            name='v2_id',
        ),
    ]
