# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CtsUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('name', models.CharField(default='', max_length=60, verbose_name='name', blank=True)),
                ('email', models.EmailField(unique=True, max_length=250, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('mobile', models.CharField(default='', max_length=45, blank=True, validators=[django.core.validators.RegexValidator('^\\+?[0-9\\-\\(\\) \\.]*$', '+999-999-999 format, + and - are optional', 'Invalid Phone Number')])),
                ('code', models.CharField(default='', max_length=45, blank=True)),
                ('skype', models.CharField(default='', max_length=50, blank=True, validators=[django.core.validators.RegexValidator('^[a-z][a-z0-9\\.,\\-_]{5,31}$', 'Skype name must be between 6-32 characters, start with a letter and contain only letters and numbers (no spaces or  special characters)', 'Invalid Skype Username')])),
                ('notes', models.TextField(default='', blank=True)),
                ('role', models.CharField(default='partner', help_text="User's main role (might imply some permissions of other roles)", max_length=20, choices=[('coordinator', 'Coordinator'), ('manager', 'Monitoring manager'), ('officer', 'Monitoring officer'), ('partner', 'Partner')])),
                ('referrer_id', models.IntegerField(null=True, blank=True)),
                ('city_id', models.IntegerField(null=True, blank=True)),
                ('colour', models.CharField(default='', max_length=7, blank=True, validators=[django.core.validators.RegexValidator('^#(?:[0-9a-fA-F]{3}){1,2}$', '#AAA or #ABCDEF hex code', 'Invalid Hex Color')])),
                ('v2_id', models.IntegerField(help_text="Only used for migration to track what the user's ID was in v2. If role is PARTNER then this was the ID of the Partners record; otherwise, it was the ID of the Users record.", null=True, blank=True)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model,),
        ),
    ]
