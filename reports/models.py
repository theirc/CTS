from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from cts.utils import USDCurrencyField


class DonorShipmentData(models.Model):
    """Aggregates data about PackageItems grouped by donor and shipment.

    Signals are used to update this table automatically when a PackageItem
    is saved or deleted.

    """
    donor = models.ForeignKey('catalog.Donor', null=True, blank=True)
    shipment = models.ForeignKey('shipments.Shipment')

    package_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of Packages in the Shipment containing at least "
                  "one PackageItem that was given by this donor.")
    item_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of PackageItems in this Shipment that were given "
                  "by this donor.")
    delivered_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of PackageItems in this Shipment that were given "
                  "by this donor and whose parent package was  delivered.")
    percentage_of_shipment = models.DecimalField(
        default=Decimal('0.00'), max_digits=5, decimal_places=4,
        help_text="Percent of PackageItems in this Shipment that were given "
                  "by this donor.")
    price_local = models.DecimalField(
        default=Decimal('0.0000'), max_digits=16, decimal_places=4,
        verbose_name="Total Price (Local)",
        validators=[MinValueValidator(0.0)],
        help_text="Total extended local price of all items given by this "
                  "Donor in this Shipment.")
    price_usd = USDCurrencyField(
        max_digits=16,
        verbose_name="Total Price (USD)",
        help_text="Total extended US price of all items given by this Donor "
                  "in this Shipment.")

    def percent_items_received(self):
        return "%d%%" % (100 * self.delivered_count // self.item_count)

    class Meta:
        unique_together = [('donor', 'shipment')]


class DonorCategoryData(models.Model):
    """Aggregates data about PackageItems grouped by donor and category.

    Signals are used to update this table automatically when a PackageItem
    is saved or deleted.

    """
    donor = models.ForeignKey('catalog.Donor', null=True, blank=True)
    category = models.ForeignKey('catalog.ItemCategory', null=True, blank=True)

    item_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of PackageItems in this Category that were given "
                  "by this Donor.")
    total_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Total quantity of PackageItems in this Category that were "
                  "given by this Donor.")
    price_local = models.DecimalField(
        default=Decimal('0.0000'), max_digits=16, decimal_places=4,
        verbose_name="Total Price (Local)",
        help_text="Total extended local price of all items given by this "
                  "Donor in this Category.")
    price_usd = USDCurrencyField(
        max_digits=16,
        verbose_name="Total Price (USD)",
        help_text="Total extended US price of all items given by this Donor "
                  "in this Category.")

    first_date_shipped = models.DateField(null=True, blank=True)
    last_date_shipped = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = [('donor', 'category')]
