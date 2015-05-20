# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
import django.contrib.gis.db.models.fields
from decimal import Decimal
import shipments.models
import django.db.models.deletion
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Kit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', unique=True, max_length=255)),
                ('description', models.CharField(default=b'', max_length=255)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KitItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=1, help_text=b'Number of this item to include in a package when making the package from this kit.')),
                ('catalog_item', models.ForeignKey(to='catalog.CatalogItem')),
                ('kit', models.ForeignKey(related_name=b'items', to='shipments.Kit')),
            ],
            options={
                'ordering': ['kit', 'catalog_item'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('longitude', models.DecimalField(max_digits=13, decimal_places=10)),
                ('latitude', models.DecimalField(max_digits=13, decimal_places=10)),
                ('altitude', models.DecimalField(default=None, null=True, max_digits=13, decimal_places=6, blank=True)),
                ('accuracy', models.DecimalField(default=None, null=True, max_digits=13, decimal_places=6, blank=True)),
                ('when', models.DateTimeField()),
            ],
            options={
                'ordering': ['-when'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=255)),
                ('description', models.CharField(default=b'', max_length=255)),
                ('number_in_shipment', models.IntegerField(help_text=b'The number assigned to this package in the shipment. Packages in a shipment are numbered, starting with 1. ')),
                ('status', models.IntegerField(default=1, null=True, blank=True, choices=[(1, b'In progress'), (2, b'Ready for pickup'), (3, b'Picked up'), (4, b'In transit'), (5, b'Received'), (6, b'Overdue'), (7, b'Lost'), (8, b'Canceled')])),
                ('code', models.CharField(unique=True, max_length=45)),
                ('kit', models.ForeignKey(blank=True, to='shipments.Kit', null=True)),
            ],
            options={
                'ordering': ['shipment', 'number_in_shipment', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PackageItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('unit', models.CharField(max_length=255, blank=True)),
                ('price_usd', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Price of one unit in US dollars', verbose_name=b'Price USD')),
                ('price_local', models.DecimalField(decimal_places=4, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0.0)], help_text=b'Price of one unit in TRY', verbose_name=b'Price TRY')),
                ('weight', models.FloatField(default=0.0, help_text=b'Weight of one unit', validators=[django.core.validators.MinValueValidator(0.0)])),
                ('quantity', models.IntegerField(default=1)),
                ('catalog_item', models.ForeignKey(blank=True, to='catalog.CatalogItem', null=True)),
                ('donor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='catalog.Donor', null=True)),
                ('donor_t1', models.ForeignKey(related_name=b't1_package_items', on_delete=django.db.models.deletion.PROTECT, blank=True, to='catalog.DonorCode', null=True)),
                ('item_category', models.ForeignKey(related_name=b'shipments_packageitem_items', on_delete=django.db.models.deletion.PROTECT, db_column=b'item_category', blank=True, to='catalog.ItemCategory', null=True)),
                ('package', models.ForeignKey(related_name=b'items', on_delete=django.db.models.deletion.PROTECT, to='shipments.Package')),
                ('supplier', models.ForeignKey(related_name=b'package_items', on_delete=django.db.models.deletion.PROTECT, blank=True, to='catalog.Supplier', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(default=b'', max_length=255)),
                ('shipment_date', models.DateField(default=datetime.date.today)),
                ('store_release', models.CharField(default=b'', max_length=45)),
                ('date_in_transit', models.DateField(null=True, blank=True)),
                ('date_picked_up', models.DateField(null=True, blank=True)),
                ('date_expected', models.DateField(null=True, blank=True)),
                ('date_received', models.DateField(null=True, blank=True)),
                ('status', models.IntegerField(default=1, choices=[(1, b'In progress'), (2, b'Ready for pickup'), (3, b'Picked up'), (4, b'In transit'), (5, b'Received'), (6, b'Overdue'), (7, b'Lost'), (8, b'Canceled')])),
                ('acceptable', models.BooleanField(default=False)),
                ('status_note', models.TextField(blank=True)),
                ('donor', models.CharField(max_length=45, null=True, blank=True)),
                ('partner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('transporter', models.ForeignKey(blank=True, to='catalog.Transporter', null=True)),
            ],
            options={
            },
            bases=(shipments.models.ShipmentMixin, models.Model),
        ),
        migrations.CreateModel(
            name='WorldBorder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('area', models.IntegerField()),
                ('pop2005', models.IntegerField(verbose_name=b'Population 2005')),
                ('fips', models.CharField(max_length=2, verbose_name=b'FIPS Code')),
                ('iso2', models.CharField(max_length=2, verbose_name=b'2 Digit ISO')),
                ('iso3', models.CharField(max_length=3, verbose_name=b'3 Digit ISO')),
                ('un', models.IntegerField(verbose_name=b'United Nations Code')),
                ('region', models.IntegerField(verbose_name=b'Region Code')),
                ('subregion', models.IntegerField(verbose_name=b'Sub-Region Code')),
                ('lon', models.FloatField()),
                ('lat', models.FloatField()),
                ('mpoly', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='package',
            name='shipment',
            field=models.ForeignKey(related_name=b'packages', on_delete=django.db.models.deletion.PROTECT, to='shipments.Shipment'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='package',
            unique_together=set([('shipment', 'number_in_shipment')]),
        ),
        migrations.AlterIndexTogether(
            name='package',
            index_together=set([('shipment', 'number_in_shipment')]),
        ),
        migrations.AddField(
            model_name='location',
            name='country',
            field=models.ForeignKey(blank=True, to='shipments.WorldBorder', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='location',
            name='package',
            field=models.ForeignKey(related_name=b'locations', to='shipments.Package'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='PackageDBView',
            fields=[
            ],
            options={
                'db_table': 'packages_view',
                'managed': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShipmentDBView',
            fields=[
            ],
            options={
                'db_table': 'shipments_view',
                'managed': False,
            },
            bases=(shipments.models.ShipmentMixin, models.Model),
        ),
    ]
