# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from decimal import Decimal
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CatalogItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('item_code', models.CharField(default='', max_length=255)),
                ('description', models.CharField(default='', max_length=255, db_index=True)),
                ('unit', models.CharField(default='', max_length=255, blank=True)),
                ('price_usd', models.DecimalField(decimal_places=2, default=Decimal('0.00'), validators=[django.core.validators.MinValueValidator(0.0)], max_digits=10, blank=True, null=True, verbose_name='Price USD')),
                ('price_local', models.DecimalField(decimal_places=4, default=Decimal('0.00'), validators=[django.core.validators.MinValueValidator(0.0)], max_digits=10, blank=True, null=True, verbose_name='Price TRY')),
                ('weight', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0)])),
            ],
            options={
                'ordering': ['item_category', 'description'],
                'db_table': 'catalog',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Donor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', unique=True, max_length=45)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DonorCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(default='', max_length=45)),
                ('donor_code_type', models.CharField(default='t1', max_length=2, choices=[('t1', 'T1'), ('t3', 'T3')])),
            ],
            options={
                'ordering': ['code'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ItemCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', max_length=100, db_index=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'item_category',
                'verbose_name_plural': 'item categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', unique=True, max_length=45)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Transporter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default='', unique=True, max_length=45)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='donorcode',
            unique_together=set([('code', 'donor_code_type')]),
        ),
        migrations.AddField(
            model_name='donor',
            name='t1_codes',
            field=models.ManyToManyField(help_text='Add a T1 Code', related_name='t1_donors', null=True, to='catalog.DonorCode', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='donor',
            name='t3_codes',
            field=models.ManyToManyField(help_text='Add a T3 Code', related_name='t3_donors', null=True, to='catalog.DonorCode', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='catalogitem',
            name='donor',
            field=models.ForeignKey(blank=True, to='catalog.Donor', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='catalogitem',
            name='donor_t1',
            field=models.ForeignKey(related_name='t1_catalog_items', blank=True, to='catalog.DonorCode', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='catalogitem',
            name='item_category',
            field=models.ForeignKey(related_name='items', db_column='item_category', to='catalog.ItemCategory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='catalogitem',
            name='supplier',
            field=models.ForeignKey(blank=True, to='catalog.Supplier', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='catalogitem',
            unique_together=set([('description', 'donor', 'supplier', 'price_local')]),
        ),
    ]
