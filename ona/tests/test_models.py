import json
from datetime import timedelta

from mock import patch

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import now

from shipments.models import PackageScan, Shipment, PackageDBView
from shipments.tests.factories import PackageFactory
from ona.models import FormSubmission
from ona.representation import PackageScanFormSubmission


QR_CODE = 'test'
PACKAGE_DATA = """
{
    "_notes": [],
    "package_count": "1",
    "_xform_id_string": "123",
    "_bamboo_dataset_id": "",
    "_tags": [],
    "community": "asdfasdf",
    "current_location": "STATUS_IN_TRANSIT-Zero_Point",
    "meta/instanceID": "uuid:2a11435f-8eaf-44f9-bd75-00a4bac8fbcd",
    "district": "asdfasdf",
    "_geolocation": ["35.7201", "-79.1772"],
    "_status": "submitted_via_web",
    "num_packages": "1",
    "today": "2014-07-25",
    "gps": "35.7201 -79.1772 0 24000",
    "complete": "yes",
    "_uuid": "2a11435f-8eaf-44f9-bd75-00a4bac8fbcd",
    "_submitted_by": null,
    "formhub/uuid": "799705ba0bd54b4d97bcf43644e4c272",
    "_id": 150250,
    "package_information/package": [
        {"package_information/package/qr_code": "test", "package_information/package/position": "1"}
    ],
    "_submission_time": "2014-07-25T17:19:15",
    "governate": "asdfasfd",
    "_attachments": [],
    "deviceid": "enketo.org:nlwPcZ7s4nDDhvk8",
    "sub_district": "asdfasdf",
    "form_id": "123",
    "form_definition": {
        "choices": {
            "location_list": [
                {"name": "STATUS_PICKED_UP-something",
                "label": {"Arabic": "Arabic picked up", "English": "English picked up"}
                 },
                {"name": "STATUS_IN_TRANSIT-Zero_Point",
                "label": {"Arabic": "Arabic Zero_Point", "English": "English Zero_Point"}
                 },
                {"name": "STATUS_RECEIVED",
                    "label": {"Arabic": "Arabic Received", "English": "English Received"}
                 }
                ]
            }
    }
}
"""

VOUCHER_DATA = """
{
    "_notes": [],
    "package_count": "1",
    "_xform_id_string": "123",
    "_bamboo_dataset_id": "",
    "_tags": [],
    "community": "asdfasdf",
    "current_location": "STATUS_IN_TRANSIT-Zero_Point",
    "meta/instanceID": "uuid:2a11435f-8eaf-44f9-bd75-00a4bac8fbcd",
    "district": "asdfasdf",
    "_geolocation": ["35.7201", "-79.1772"],
    "_status": "submitted_via_web",
    "num_packages": "1",
    "today": "2014-07-25",
    "gps": "35.7201 -79.1772 0 24000",
    "complete": "yes",
    "_uuid": "2a11435f-8eaf-44f9-bd75-00a4bac8fbcd",
    "_submitted_by": null,
    "formhub/uuid": "799705ba0bd54b4d97bcf43644e4c272",
    "_id": 150250,
    "voucher_information/qr_code": "test",
    "_submission_time": "2014-07-25T17:19:15",
    "governate": "asdfasfd",
    "_attachments": [],
    "deviceid": "enketo.org:nlwPcZ7s4nDDhvk8",
    "sub_district": "asdfasdf",
    "form_id": "123",
    "form_definition": {
        "choices": {
            "location_list": [
                {"name": "STATUS_PICKED_UP-something",
                "label": {"Arabic": "Arabic picked up", "English": "English picked up"}
                 },
                {"name": "STATUS_IN_TRANSIT-Zero_Point",
                "label": {"Arabic": "Arabic Zero_Point", "English": "English Zero_Point"}
                 },
                {"name": "STATUS_RECEIVED",
                    "label": {"Arabic": "Arabic Received", "English": "English Received"}
                 }
                ]
            }
    }
}
"""

USER_CODE_DATA = """
{
    "_notes": [],
    "meta/instanceID": "uuid:e99e6c4e-3081-4272-9bd0-8f06d65a2a21",
    "end": "2014-09-25T08:08:03.000-04:00",
    "imei": "enketo.org:oyq1aWdj8ekhH4iX",
    "_submission_time": "2014-09-25T12:08:08",
    "_uuid": "e99e6c4e-3081-4272-9bd0-8f06d65a2a21",
    "_bamboo_dataset_id": "",
    "_tags": [],
    "qr_code": "test",
    "_geolocation": [
        null,
        null
    ],
    "start": "2014-09-25T08:07:58.000-04:00",
    "_submitted_by": null,
    "phonenumber": "no phonenumber property in enketo",
    "deviceid": "device_foo",
    "_attachments": [],
    "_xform_id_string": "user_device_capture",
    "_status": "submitted_via_web",
    "_id": 403799,
    "today": "2014-09-25",
    "formhub/uuid": "1dd63c0e7254435ebd4ddf0e48f366d9",
    "form_id": "111"
}
"""


@override_settings(ONA_PACKAGE_FORM_IDS=[123, 456], ONA_DEVICEID_VERIFICATION_FORM_ID=111)
class FormSubmissionTestCase(TestCase):
    def test_record_package_location(self):
        PackageFactory(code=QR_CODE)
        self.assertFalse(PackageScan.objects.all())
        form_data = PackageScanFormSubmission(json.loads(PACKAGE_DATA))
        FormSubmission.from_ona_form_data(form_data)
        self.assertTrue(PackageScan.objects.all())

    def test_record_voucher_location(self):
        PackageFactory(code=QR_CODE)
        self.assertFalse(PackageScan.objects.all())
        form_data = PackageScanFormSubmission(json.loads(VOUCHER_DATA))
        FormSubmission.from_ona_form_data(form_data)
        self.assertTrue(PackageScan.objects.all())

    def test_record_package_scan_no_gps(self):
        # A scan with no GPS data still updates the package status
        pkg = PackageFactory(code=QR_CODE, status=Shipment.STATUS_IN_PROGRESS)
        self.assertFalse(PackageScan.objects.all())
        data = json.loads(PACKAGE_DATA)
        data.pop('gps')
        form_data = PackageScanFormSubmission(data)
        FormSubmission.from_ona_form_data(form_data)
        # Yes, we have a scan
        self.assertTrue(PackageScan.objects.all())
        self.assertEqual(Shipment.STATUS_IN_TRANSIT, PackageDBView.objects.get(pk=pkg.pk).status)

    @patch('ona.models.logger')
    def test_record_package_location_no_package(self, mock_logging):
        """No matching package with the supplied QR code is found"""
        PackageFactory(code='not-found')
        self.assertFalse(PackageScan.objects.all())
        form_data = PackageScanFormSubmission(json.loads(PACKAGE_DATA))
        FormSubmission.from_ona_form_data(form_data)
        self.assertFalse(PackageScan.objects.all())
        self.assertTrue(mock_logging.exception.called)

    @patch('ona.models.logger')
    def test_record_package_location_malformed_uuid(self, mock_logging):
        """Bad UUID"""
        PackageFactory(code=QR_CODE)
        self.assertFalse(PackageScan.objects.all())
        data = json.loads(PACKAGE_DATA)
        data['_uuid'] = 'foobar'
        form_data = PackageScanFormSubmission(data)
        FormSubmission.from_ona_form_data(form_data)
        self.assertFalse(PackageScan.objects.all())
        self.assertTrue(mock_logging.exception.called)

    @patch('ona.models.logger')
    def test_record_package_location_valid_status_picked_up(self, mock_logging):
        """Valid current_location ingested"""
        PackageFactory(code=QR_CODE)
        self.assertFalse(PackageScan.objects.all())
        data = json.loads(PACKAGE_DATA)
        data['current_location'] = "STATUS_PICKED_UP-something"
        form_data = PackageScanFormSubmission(data)
        FormSubmission.from_ona_form_data(form_data)
        self.assertFalse(mock_logging.error.called)
        scan = PackageScan.objects.all()[0]
        self.assertEqual(scan.package.status, Shipment.STATUS_PICKED_UP)
        self.assertEqual(scan.package.shipment.status, Shipment.STATUS_PICKED_UP)
        self.assertEqual(scan.package.date_picked_up, form_data._submission_time)
        self.assertEqual(scan.package.date_in_transit, None)
        self.assertEqual(scan.package.date_received, None)

    @patch('ona.models.logger')
    def test_record_package_location_valid_status_in_transit(self, mock_logging):
        """Valid current_location ingested"""
        date_picked_up = now()
        PackageFactory(code=QR_CODE, date_picked_up=date_picked_up)
        self.assertFalse(PackageScan.objects.all())
        data = json.loads(PACKAGE_DATA)
        form_data = PackageScanFormSubmission(data)
        FormSubmission.from_ona_form_data(form_data)
        self.assertFalse(mock_logging.error.called)
        scan = PackageScan.objects.all()[0]
        self.assertEqual(scan.package.status, Shipment.STATUS_IN_TRANSIT)
        self.assertEqual(scan.package.shipment.status, Shipment.STATUS_IN_TRANSIT)
        self.assertEqual(scan.package.date_picked_up, date_picked_up)
        self.assertEqual(scan.package.date_in_transit, form_data._submission_time)
        self.assertEqual(scan.package.date_received, None)

    @patch('ona.models.logger')
    def test_record_package_location_valid_status_received(self, mock_logging):
        """Valid current_location ingested"""
        date_picked_up = now() - timedelta(days=1)
        date_in_transit = now()
        PackageFactory(code=QR_CODE, date_picked_up=date_picked_up, date_in_transit=date_in_transit)
        self.assertFalse(PackageScan.objects.all())
        data = json.loads(PACKAGE_DATA)
        data['current_location'] = "STATUS_RECEIVED"
        form_data = PackageScanFormSubmission(data)
        FormSubmission.from_ona_form_data(form_data)
        self.assertFalse(mock_logging.error.called)
        scan = PackageScan.objects.all()[0]
        self.assertEqual(scan.package.status, Shipment.STATUS_RECEIVED)
        self.assertEqual(scan.package.shipment.status, Shipment.STATUS_RECEIVED)
        self.assertEqual(scan.package.date_picked_up, date_picked_up)
        self.assertEqual(scan.package.date_in_transit, date_in_transit)
        self.assertEqual(scan.package.date_received, form_data._submission_time)

    @patch('ona.models.logger')
    def test_record_package_location_invalid_status(self, mock_logging):
        """Invalid current_location ingested"""
        PackageFactory(code=QR_CODE)
        self.assertFalse(PackageScan.objects.all())
        data = json.loads(PACKAGE_DATA)
        data["current_location"] = "FOOBAR-Zero_Point"
        form_data = PackageScanFormSubmission(data)
        FormSubmission.from_ona_form_data(form_data)
        self.assertTrue(mock_logging.error.called)
