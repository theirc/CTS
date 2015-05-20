"""
This file has a first pass at some of the models we'll
need outside of the first app we plan to implement. These
are based on running `inspectdb` on a database. They will
probably need more work.
"""
from __future__ import unicode_literals

from django.db import models


class Donor(models.Model):
    donor_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)
    donor_t1 = models.CharField(max_length=45, blank=True)
    donor_t3 = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'donors'

    def __unicode__(self):
        return self.name


class Partner(models.Model):
    partner_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)
    colour = models.CharField(max_length=7, blank=True)
    code = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'partners'

    def __unicode__(self):
        return self.name


class PartnerUser(models.Model):
    partner = models.ForeignKey('entities.Partner', db_column='partner_id')
    user = models.ForeignKey('entities.User', db_column='user_id')

    class Meta:
        db_table = 'partners_users'


class Supplier(models.Model):
    supplier_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'suppliers'

    def __unicode__(self):
        return self.name


class User(models.Model):
    user_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)
    email = models.CharField(max_length=45, blank=True)
    role = models.ForeignKey('misc.Role', blank=True, null=True)
    password = models.CharField(max_length=45, blank=True)
    mobile = models.CharField(max_length=45, blank=True)
    code = models.CharField(max_length=45, blank=True)
    referrer_id = models.IntegerField(blank=True, null=True)
    city = models.ForeignKey('misc.City', blank=True, null=True)
    skype = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'users'

    def __unicode__(self):
        return self.name


class Action(models.Model):
    action_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'actions'

    def __unicode__(self):
        return self.name


class City(models.Model):
    city_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'cities'
        verbose_name_plural = 'cities'

    def __unicode__(self):
        return self.name


class Handset(models.Model):
    handset_id = models.IntegerField(primary_key=True)
    device_id = models.CharField(unique=True, max_length=45, blank=True)
    user = models.ForeignKey('entities.User', blank=True, null=True, related_name='handsets')
    partner_id = models.IntegerField(blank=True, null=True)
    alias = models.CharField(max_length=45)

    class Meta:
        db_table = 'handsets'


class Location(models.Model):
    # id = models.IntegerField(primary_key=True)
    package = models.ForeignKey('packages.Package', blank=True, null=True)
    location = models.CharField(max_length=45, blank=True)
    date = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'locations'

    def __unicode__(self):
        return self.location


class Role(models.Model):
    role_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'roles'

    def __unicode__(self):
        return self.name


class RoleAction(models.Model):
    role = models.ForeignKey(Role)
    action = models.ForeignKey(Action)

    class Meta:
        db_table = 'roles_actions'


class StatusCode(models.Model):
    status_code = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)

    class Meta:
        db_table = 'status_codes'


class Package(models.Model):
    package_id = models.IntegerField(primary_key=True)
    shipment = models.ForeignKey('packages.Shipment', blank=True, null=True)
    code = models.CharField(max_length=45, blank=True)
    status = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=45, blank=True)
    template_id = models.IntegerField(blank=True, null=True)
    num_items = models.IntegerField(blank=True, null=True)
    value = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'packages'


class PackageItem(models.Model):
    package = models.ForeignKey(Package)
    item = models.ForeignKey('catalog.CatalogItem')
    donor = models.ForeignKey('entities.Donor')
    supplier = models.ForeignKey('entities.Supplier', blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    num_items = models.IntegerField(blank=True, null=True)
    value = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = 'packages_items'


class PackageTemplate(models.Model):
    template_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'package_templates'


class PackageTemplateItem(models.Model):
    template_id = models.IntegerField()
    item = models.ForeignKey('catalog.CatalogItem')
    price = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'package_template_items'


class Shipment(models.Model):
    shipment_id = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=255, blank=True)
    transporter = models.ForeignKey('entities.User', blank=True, null=True)
    partner = models.ForeignKey('entities.Partner', blank=True, null=True)
    expected_duration = models.IntegerField(blank=True, null=True)
    shipment_date = models.DateField(blank=True, null=True)
    store_release = models.CharField(max_length=45, blank=True)
    status = models.IntegerField()
    acceptable = models.IntegerField(blank=True, null=True)
    status_note = models.TextField(blank=True)
    num_items = models.IntegerField(blank=True, null=True)
    value = models.FloatField(blank=True, null=True)
    nfi = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'shipments'


class TrackingForm(models.Model):
    form_id = models.IntegerField(primary_key=True)
    device_id = models.CharField(max_length=45, blank=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    num_packages = models.IntegerField(blank=True, null=True)
    qr1 = models.CharField(max_length=45, blank=True)
    qr2 = models.CharField(max_length=45, blank=True)
    qr3 = models.CharField(max_length=45, blank=True)
    qr4 = models.CharField(max_length=45, blank=True)
    qr5 = models.CharField(max_length=45, blank=True)
    qr6 = models.CharField(max_length=45, blank=True)
    qr7 = models.CharField(max_length=45, blank=True)
    qr8 = models.CharField(max_length=45, blank=True)
    qr9 = models.CharField(max_length=45, blank=True)
    qr10 = models.CharField(max_length=45, blank=True)
    city = models.CharField(max_length=45, blank=True)
    country = models.CharField(max_length=45, blank=True)
    inventory_checked = models.IntegerField(blank=True, null=True)
    inventory_complete = models.IntegerField(blank=True, null=True)
    send_receive = models.IntegerField(blank=True, null=True)
    location = models.CharField(max_length=45, blank=True)
    status = models.CharField(max_length=45, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'tracking_forms'


class VerificationForm(models.Model):
    form_id = models.IntegerField(primary_key=True)
    device_id = models.CharField(max_length=45, blank=True)
    qr_code = models.CharField(max_length=45, blank=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'verification_forms'
