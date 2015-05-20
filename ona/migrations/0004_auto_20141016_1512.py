# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ona', '0003_auto_20140930_1520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formsubmission',
            name='submission_time',
            field=models.DateTimeField(help_text=b'Copied from the hstore data'),
        ),
    ]
