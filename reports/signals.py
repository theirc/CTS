from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save

from shipments.models import PackageItem, Shipment

from .models import DonorCategoryData, DonorShipmentData


@receiver(post_save, sender=PackageItem)
@receiver(post_delete, sender=PackageItem)
def update_reports_from_item_signal(instance, **kwargs):
    donor_id = instance.donor_id
    category_id = instance.item_category_id
    shipment_id = instance.package.shipment_id
    _update_donor_shipment_data(donor_id, shipment_id)
    _update_donor_category_data(donor_id, category_id)


def _update_donor_category_data(donor_id, category_id):
    items = PackageItem.objects.filter(donor_id=donor_id, item_category_id=category_id)
    if not items:
        DonorCategoryData.objects.filter(donor_id=donor_id, category_id=category_id).delete()
    else:
        data, _ = DonorCategoryData.objects.get_or_create(donor_id=donor_id,
                                                          category_id=category_id)
        data.item_count = len(items)
        data.total_quantity = sum(i.quantity for i in items)
        data.price_local = sum(i.extended_price_local for i in items)
        data.price_usd = sum(i.extended_price_usd for i in items)
        shipments = Shipment.objects.filter(packages__items__in=items)
        data.first_date_shipped = shipments.order_by('shipment_date').first().shipment_date
        data.last_date_shipped = shipments.order_by('-shipment_date').first().shipment_date
        data.save()


def _update_donor_shipment_data(donor_id, shipment_id):
    items = PackageItem.objects.filter(donor_id=donor_id, package__shipment_id=shipment_id)
    if not items.exists():
        DonorShipmentData.objects.filter(donor_id=donor_id, shipment_id=shipment_id).delete()
    else:
        num_items = len(items)
        all_shipment_items = PackageItem.objects.filter(package__shipment_id=shipment_id)
        all_shipment_items_count = all_shipment_items.count()
        data, _ = DonorShipmentData.objects.get_or_create(donor_id=donor_id,
                                                          shipment_id=shipment_id)
        data.item_count = num_items
        data.delivered_count = items.filter(package__status=Shipment.STATUS_RECEIVED).count()
        data.package_count = len(set(i.package_id for i in items))
        if all_shipment_items_count:
            data.percentage_of_shipment = float(num_items) / all_shipment_items_count
        else:
            data.percentage_of_shipment = 0.0
        data.price_local = sum(i.extended_price_local for i in items)
        data.price_usd = sum(i.extended_price_usd for i in items)
        data.save()
