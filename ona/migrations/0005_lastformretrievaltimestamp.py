# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ona.models


class Migration(migrations.Migration):

    dependencies = [
        ('ona', '0004_auto_20141016_1512'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastFormRetrievalTimestamp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('form_id', models.IntegerField()),
                ('timestamp', models.DateTimeField(default=ona.models.minimum_aware_datetime)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
