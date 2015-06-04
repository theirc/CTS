from __future__ import absolute_import
import logging

from django.conf import settings

from requests import ConnectionError

from accounts.models import CtsUser
from cts.celery import app
from ona.api import OnaApiClient, OnaApiClientException
from ona.models import FormSubmission, LastFormRetrievalTimestamp
from ona.representation import PackageScanFormSubmission, OnaItemBase


logger = logging.getLogger(__name__)

# If we get an error looking up a form, we remember it here so we don't keep
# trying it again
bad_form_ids = set()


def reset_bad_form_ids():
    bad_form_ids.clear()


@app.task(ignore_result=True)
def process_new_package_scans():
    """Updates the local database with new package tracking form submissions"""
    logger.debug("process_new_package_scans task starting...")
    try:
        form_id = int(settings.ONA_PACKAGE_FORM_ID)
        if form_id in bad_form_ids:
            return

        client = OnaApiClient()
        form_def = client.get_form_definition(form_id)

        if not form_def:
            # Logging an error should result in an email to the admins so they
            # know to fix this.
            logger.error("Bad ONA_PACKAGE_FORM_ID: %s" % form_id)
            # Let's not keep trying for the bad form ID. We'll have to change the
            # settings and restart to fix it.
            bad_form_ids.add(form_id)
            return

        # What's the last submission we got (if any)
        most_recent_submission = FormSubmission.objects.filter(form_id=form_id)\
            .order_by('-submission_time').first()
        if most_recent_submission:
            # Don't re-fetch the last form
            since = most_recent_submission.submission_time
            logger.debug("Getting forms since %s" % since)
        else:
            logger.debug("No form submissions yet for %r" % form_id)
            since = None

        submissions = client.get_form_submissions(form_id, since=since)
        logger.debug("process_new_package_scans downloaded %d submitted forms" % len(submissions))
        # add the form definition JSON to each submission
        for data in submissions:
            data.update({'form_id': form_id})
            data.update({'form_definition': form_def})
        # create a list of API repr objects and ensure they are sorted by submission date
        objects = [PackageScanFormSubmission(x) for x in submissions]
        objects.sort(key=lambda x: x._submission_time)
        logger.debug("There are %d objects to look at" % len(objects))
        for submission in objects:
            existing = FormSubmission.objects.filter(uuid=submission._uuid).first()
            if not existing:
                logger.debug("Got new form, creating new record")
                try:
                    FormSubmission.from_ona_form_data(submission)
                except Exception:
                    logger.exception("HEY got exception creating new FormSubmission")
            else:
                logger.debug("Form %s (%r, %s) already existed" % (submission._uuid,
                                                                   submission.form_id,
                                                                   existing.submission_time))
    except ConnectionError:
        logger.exception("Error connecting to Ona server")
    except Exception:
        logger.exception("Something blew up in process_new_package_scans")
    logger.debug("process_new_package_scans task done")


@app.task(ignore_result=True)
def verify_deviceid():
    """Store the DeviceID and QR code"""
    last_retrieval = None
    try:
        form_id = settings.ONA_DEVICEID_VERIFICATION_FORM_ID
        if form_id in bad_form_ids:
            return

        client = OnaApiClient()

        # Make sure the form exists before we try to get submissions
        form_defn = client.get_form_definition(form_id)
        if not form_defn:
            # Logging an error should result in an email to the admins so they
            # know to fix this.
            logger.error("Bad ONA_DEVICEID_VERIFICATION_FORM_ID: %s" % form_id)
            # Let's not keep trying for the bad form ID. We'll have to change the
            # settings and restart to fix it.
            bad_form_ids.add(form_id)
            return

        last_retrieval, unused = LastFormRetrievalTimestamp.objects.get_or_create(form_id=form_id)

        try:
            submissions = client.get_form_submissions(form_id, since=last_retrieval.timestamp)
        except OnaApiClientException as e:
            if e.status_code != 404:
                raise
            logger.error("Form %s not found at Ona" % form_id)
            return
        # add the form definition JSON to each submission
        for data in submissions:
            data.update({'form_id': form_id})
        # create a list of API repr objects and ensure they are sorted by submission date
        objects = [OnaItemBase(x) for x in submissions]
        objects.sort(key=lambda x: x._submission_time)
        for submission in objects:
            if submission._submission_time > last_retrieval.timestamp:
                last_retrieval.timestamp = submission._submission_time
            valid_code = CtsUser.objects.filter(code=submission.qr_code).exists()
            if valid_code:
                if not FormSubmission.objects.filter(uuid=submission._uuid).exists():
                    FormSubmission.from_ona_form_data(submission)
            else:
                # Log an invalid QR Code
                msg = "FormSubmission with form id of %s has invalid User QR Code: %s" \
                    % (submission._xform_id_string, submission.qr_code)
                logger.error(msg)
    except ConnectionError:
        logger.exception("Error connecting to Ona server")
    except Exception:
        logger.exception("Something blew up in verify_deviceid")
    finally:
        if last_retrieval:
            last_retrieval.save()
