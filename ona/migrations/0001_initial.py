# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
from django.contrib.postgres.fields import HStoreField


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FormSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('form_id', models.CharField(max_length=256)),
                ('uuid', models.CharField(max_length=36, validators=[django.core.validators.RegexValidator(regex=b'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', message=b'Requires a 36 character UUID v4 formatted string', code=b'nomatch')])),
                ('data', HStoreField(help_text=b'Hstore of Ona form submission')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
