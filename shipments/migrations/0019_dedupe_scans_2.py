# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.models.aggregates import Max
from django.db.models.deletion import SET_NULL


def no_op(apps, schema_editor):
    pass



def dedupe_scans(apps, schema_editor):
    PackageScan = apps.get_model('shipments', 'PackageScan')
    all_scans = PackageScan.objects.all()
    if not all_scans.exists():
        return

    print("\nDeduping package scans")
    print("There are %10d scans" % all_scans.count())

    fields = ['package_id', 'when']
    unique_scans = PackageScan.objects.order_by(*fields).distinct(*fields)
    saved_unique_scans = list(unique_scans)

    print("There are %10d unique scans" % len(saved_unique_scans))


    print("Truncating the table...")
    cursor = schema_editor.connection.cursor()
    cursor.execute("TRUNCATE %s" % PackageScan._meta.db_table)

    print("Re-loading the unique scans...")
    next_pk = 1
    for scan in saved_unique_scans:
        scan.pk = next_pk
        scan.save()
        next_pk += 1
    print("last PK: %s" % scan.pk)

    update_postgres_sequence_generator(PackageScan, schema_editor.connection)

    # Get new status - make sure we fixed things :-)
    all_scans = PackageScan.objects.all()
    print("There are %10d scans" % all_scans.count())
    unique_scans = PackageScan.objects.order_by(*fields).distinct(*fields)
    print("There are %10d unique scans" % unique_scans.count())
    print("Done deduping")

def update_postgres_sequence_generator(model, connection):
    """
    Update the sequence generator for a model's primary key
    to the max current value of that key, so that Postgres
    will know not to try to use the previously-used values again.

    Apparently this is needed because when we create objects
    during the migration, we specify the primary key's value,
    so the Postgres sequence doesn't get used or incremented.

    :param db: Key for the database setting for the database to use
    """
    table_name = model._meta.db_table
    attname, colname = model._meta.pk.get_attname_column()
    seq_name = "%s_%s_seq" % (table_name, colname)
    max_val = model.objects.aggregate(maxkey=Max(attname))['maxkey'] or 1
    cursor = connection.cursor()
    cursor.execute("select setval(%s, %s);", [seq_name, max_val])

class Migration(migrations.Migration):

    dependencies = [
        ('shipments', '0018_dedupe_scans'),
    ]

    operations = [
        migrations.RunPython(dedupe_scans, no_op),
        migrations.AddField(
            model_name='package',
            name='last_scan',
            field=models.ForeignKey(related_name='last_packages', on_delete=SET_NULL, blank=True, to='shipments.PackageScan', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='package',
            name='last_scan_status_label',
            field=models.CharField(max_length=128, null=True, blank=True),
            preserve_default=True,
        ),
    ]
