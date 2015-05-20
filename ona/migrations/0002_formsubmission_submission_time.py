# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import now


default_submission_time = now()


class Migration(migrations.Migration):

    dependencies = [
        ('ona', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='formsubmission',
            name='submission_time',
            field=models.DateTimeField(default=default_submission_time),
            preserve_default=False,
        ),
    ]
