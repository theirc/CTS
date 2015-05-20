from datetime import datetime
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.dispatch import receiver
from django.db import models
from django.db.models.signals import post_save
from django.utils.timezone import make_aware, utc

from django_hstore import hstore

from accounts.models import CtsUser
from shipments.models import PackageScan, Package, Shipment

from ona.representation import OnaItemBase, PackageScanFormSubmission


logger = logging.getLogger(__name__)

UUID_REGEX = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


class FormSubmission(models.Model):
    form_id = models.CharField(max_length=256)
    uuid = models.CharField(
        max_length=36,
        validators=[RegexValidator(
            regex=UUID_REGEX,
            message='Requires a 36 character UUID v4 formatted string',
            code='nomatch')
        ]
    )

    data = hstore.DictionaryField(
        help_text='Hstore of Ona form submission')

    submission_time = models.DateTimeField(help_text="Copied from the hstore data")

    objects = hstore.HStoreManager()

    @staticmethod
    def from_ona_form_data(submission):
        """
        Create and return a new FormSubmission based on form data received from a
        mobile form submission
        """
        logger.info("Creating FormSubmission")
        uuid = submission._uuid
        obj = FormSubmission(
            form_id=submission.form_id,
            uuid=uuid,
            submission_time=submission._submission_time,
            data=submission.json,
        )
        try:
            obj.clean_fields()
        except ValidationError:
            logger.exception("FormSubmission with malformed uuid %s not imported" % uuid)
        else:
            obj.save()


# datetime.min is too early for strftime, go figure:
# "ValueError: year=1 is before 1900; the datetime strftime() methods require year >= 1900"
MIN_DATETIME = make_aware(datetime(2010, 1, 1, tzinfo=None), utc)


def minimum_aware_datetime():
    """A datetime earlier than any of our forms"""
    # Has to be a callable because Django migrations won't let us set the default
    # for a DateTimeField to an aware datetime, but we can use a callable.
    return MIN_DATETIME


class LastFormRetrievalTimestamp(models.Model):
    """
    Track the timestamp on the last form of each type that we retrieved, so
    we don't keep re-retrieving the same ones.
    """
    form_id = models.IntegerField()
    timestamp = models.DateTimeField(
        default=minimum_aware_datetime,
    )


@receiver(post_save, sender=FormSubmission)
def record_package_location(sender, instance, **kwargs):
    # Only record package locations for package tracking forms
    try:
        logger.debug("record_package_location...")
        form_id = int(settings.ONA_PACKAGE_FORM_ID)
        if kwargs.get('created', False) and int(instance.data['form_id']) == form_id:
            submission = PackageScanFormSubmission(instance.data)
            logger.debug("New formsubmission. %d QR codes", len(submission.get_qr_codes()))
            for code in submission.get_qr_codes():
                logger.debug("QR code: %s" % code)
                try:
                    pkg = Package.objects.get(code=code)
                except Package.DoesNotExist:
                    logger.exception("Scanned Package with code %s not found" % code)
                else:
                    scan_status_label = submission.get_current_packagescan_label()
                    PackageScan.objects.create(
                        package=pkg,
                        longitude=submission.get_lng(),
                        latitude=submission.get_lat(),
                        altitude=submission.get_altitude(),
                        accuracy=submission.get_accuracy(),
                        when=submission._submission_time,
                        status_label=scan_status_label
                    )
                    logger.debug("created location")
                    # Update Package and Shipment Status based on selected current_location value
                    # Values should look similar to the following samples, defined by the
                    # Ona XLSFOrm:
                    # STATUS_IN_TRANSIT-Zero_Point
                    # STATUS_IN_TRANSIT-Partner_Warehouse
                    # STATUS_IN_TRANSIT-Pre-Distribution_Point
                    # STATUS_RECEIVED-Distribution Point
                    # STATUS_RECEIVED-Post-Distribution Point
                    # The prefix part (before the first -) is one of the predefined status
                    # names that are attributes of the Shipment model.
                    status = submission.current_location.split('-', 1)[0]
                    logger.debug("status=%r" % status)
                    if not hasattr(Shipment, status):
                        # If no match is found, log the invalid package status as it is
                        # indicative of the app and Ona being out of sync
                        msg = "FormSubmission with form id of %s has invalid package status: %s" \
                            % (instance.form_id, status)
                        logger.error(msg)
                        continue
                    status = getattr(Shipment, status, None)
                    if status:
                        update_fields = ['last_scan_status_label']
                        pkg.last_scan_status_label = scan_status_label
                        if pkg.status != status:
                            update_fields.append('status')
                            pkg.status = status
                        if status == Shipment.STATUS_RECEIVED and not pkg.date_received:
                            update_fields.append('date_received')
                            pkg.date_received = submission._submission_time
                        elif status == Shipment.STATUS_PICKED_UP and not pkg.date_picked_up:
                            update_fields.append('date_picked_up')
                            pkg.date_picked_up = submission._submission_time
                        elif status == Shipment.STATUS_IN_TRANSIT and not pkg.date_in_transit:
                            update_fields.append('date_in_transit')
                            pkg.date_in_transit = submission._submission_time
                        pkg.save(update_fields=update_fields)
                        pkg.shipment.status = status
                        pkg.shipment.last_scan_status_label = scan_status_label
                        pkg.shipment.save(update_fields=['status', 'last_scan_status_label'])
                        logger.debug("set status to %s" % pkg.get_status_display())
        else:
            logger.debug("Ignoring this FormSubmission.  kwargs[created]=%s, form_id=%s,"
                         " form_id=%s"
                         % (kwargs.get('created', False), int(instance.data['form_id']),
                            form_id))
    except Exception:
        logger.exception("Something blew up in record_package_location")


@receiver(post_save, sender=FormSubmission)
def update_device_binding(sender, instance, **kwargs):
    # Only record package locations for package tracking forms
    form_id = int(settings.ONA_DEVICEID_VERIFICATION_FORM_ID)
    if kwargs.get('created', False) and int(instance.data['form_id']) == form_id:
        submission = OnaItemBase(instance.data)
        try:
            this_user = CtsUser.objects.get(code=submission.qr_code)
        except CtsUser.DoesNotExist:
            logger.error("Got device ID scan with code that has no matching user (%s)",
                         submission.qr_code)
            return

        # Remove this device from any user(s)
        CtsUser.objects.filter(deviceid=submission.deviceid).update(deviceid='')
        # Give to the current user
        this_user.deviceid = submission.deviceid
        this_user.save()
