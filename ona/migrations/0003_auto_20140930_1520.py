# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime

from django.db import models, migrations
import pytz


def set_submission_times(apps, schema_editor):
    FormSubmission = apps.get_model("ona", "FormSubmission")
    _date_format = '%Y-%m-%dT%H:%M:%S'

    for item in FormSubmission.objects.all():
        value = item.data['_submission_time']
        value = datetime.datetime.strptime(value, _date_format).replace(tzinfo=pytz.UTC)
        item.submission_time = value
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('ona', '0002_formsubmission_submission_time'),
    ]

    operations = [
        migrations.RunPython(set_submission_times)
    ]
