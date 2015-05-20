from __future__ import unicode_literals
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from cts.utils import USDCurrencyField
from currency.currencies import format_currency, quantize_local


class DonorCode(models.Model):
    T1 = 't1'
    T3 = 't3'
    DONOR_CODE_CHOICES = (
        (T1, 'T1'),
        (T3, 'T3'),
    )

    code = models.CharField(max_length=45, default='')
    donor_code_type = models.CharField(
        max_length=2,
        choices=DONOR_CODE_CHOICES,
        default=T1)

    def __unicode__(self):
        return self.code

    class Meta:
        ordering = ['code']
        unique_together = [
            ('code', 'donor_code_type'),
        ]


class Donor(models.Model):
    name = models.CharField(max_length=45, unique=True, default='')
    t1_codes = models.ManyToManyField(
        'DonorCode',
        limit_choices_to={'donor_code_type': DonorCode.T1},
        related_name='t1_donors',
        help_text='Add a T1 Code',
        blank=True, null=True)
    t3_codes = models.ManyToManyField(
        'DonorCode',
        limit_choices_to={'donor_code_type': DonorCode.T3},
        related_name='t3_donors',
        help_text='Add a T3 Code',
        blank=True, null=True)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name', ]


class Supplier(models.Model):
    name = models.CharField(max_length=45, unique=True, default='')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name', ]

    def is_deletable(self):
        # May only delete a supplier if no shipments have gone out
        from shipments.models import Shipment

        shipped_items = self.package_items.filter(package__status__gte=Shipment.STATUS_PICKED_UP)
        return not shipped_items.exists()


class Transporter(models.Model):
    name = models.CharField(max_length=45, unique=True, default='')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name', ]


class CatalogItem(models.Model):
    item_code = models.CharField(max_length=255, default='')
    description = models.CharField(max_length=255, db_index=True, default='')
    unit = models.CharField(max_length=255, blank=True, default='')
    price_usd = USDCurrencyField(
        verbose_name='Price USD')
    price_local = models.DecimalField(
        max_digits=10,
        # Just set decimal places as large as we're likely to need.
        # We'll validate more specifically elsewhere depending on the local currency.
        decimal_places=4,
        default=quantize_local(Decimal('0.0000')),
        validators=[MinValueValidator(0.0)],
        verbose_name='Price in local currency',
    )
    item_category = models.ForeignKey('ItemCategory', db_column='item_category',
                                      db_index=True,
                                      related_name='items')
    donor = models.ForeignKey(Donor, blank=True, null=True)
    donor_t1 = models.ForeignKey(
        DonorCode,
        limit_choices_to={'donor_code_type': DonorCode.T1},
        related_name='t1_catalog_items',
        blank=True, null=True)
    supplier = models.ForeignKey(Supplier, blank=True, null=True)
    weight = models.FloatField(default=0.0,
                               validators=[MinValueValidator(0.0)],
                               blank=True,
                               null=True)

    class Meta:
        db_table = 'catalog'
        ordering = ['item_category', 'description']
        unique_together = [
            # "The system should not allow duplicate records with matching data across
            # Description, Donor, Supplier, Local Currency Cost"
            ('description', 'donor', 'supplier', 'price_local'),
        ]

    def __unicode__(self):
        return self.description

    def formatted_price_usd(self):
        if self.price_usd:
            return format_currency('USD', self.price_usd, symbol=True, grouping=True,
                                   international=False)

    def formatted_price_local(self):
        if self.price_local:
            return format_currency(settings.LOCAL_CURRENCY, self.price_local, symbol=True,
                                   grouping=True, international=False)

    def save(self, *args, **kwargs):
        # Force local price to not have more decimal places than it should
        if self.price_local is not None:
            self.price_local = quantize_local(Decimal(self.price_local))
        super(CatalogItem, self).save(*args, **kwargs)

    def form_field_name(self):
        return "quantity-%d" % self.pk


class ItemCategory(models.Model):
    name = models.CharField(max_length=100, db_index=True, default='')

    class Meta:
        ordering = ['name']
        db_table = 'item_category'
        verbose_name_plural = 'item categories'

    def __unicode__(self):
        return self.name
