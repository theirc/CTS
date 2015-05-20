from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save

from shipments.models import PackageScan


@receiver(post_save, sender=PackageScan)
@receiver(post_delete, sender=PackageScan)
def process_last_scan_signal(instance, **kwargs):
    _update_last_scan(instance.package)


def _update_last_scan(package):
    locs = package.scans.order_by('-when')[:1]
    if not locs:
        package.last_scan = None
    else:
        package.last_scan = locs[0]
    package.save()
