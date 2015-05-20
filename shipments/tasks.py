import logging
from celery.task import task
from shipments.models import Shipment


logger = logging.getLogger(__name__)


@task
def delete_shipment(shipment_id):
    """
    Task to delete a shipment, because it can take more than 60 seconds.
    """
    try:
        try:
            shipment = Shipment.objects.get(pk=shipment_id)
        except Shipment.DoesNotExist:
            logger.error("In delete_shipment task, no shipment with id %s" % shipment_id)
        else:
            shipment.fast_delete()
    except Exception:
        logger.exception("Unexpected error in delete_shipment")
