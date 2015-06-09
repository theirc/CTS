import json

from copy import deepcopy
from mock import patch, ANY
from django.conf import settings

from django.test import TestCase
from django.test.utils import override_settings

from accounts.models import CtsUser
from accounts.tests.factories import CtsUserFactory
from ona.representation import OnaItemBase
from shipments.models import PackageScan, Shipment
from shipments.tests.factories import PackageFactory
from ona.models import FormSubmission, minimum_aware_datetime
from ona.tasks import process_new_package_scans, verify_deviceid, reset_bad_form_ids, bad_form_ids
from ona.tests.test_models import PACKAGE_DATA, USER_CODE_DATA, QR_CODE


@override_settings(
    ONA_API_ACCESS_TOKEN='foo',
    ONA_DEVICEID_VERIFICATION_FORM_ID=111,
    ONA_PACKAGE_FORM_ID=123,
    ONA_DOMAIN='ona.io'
)
@patch('ona.tasks.OnaApiClient.get_form_submissions')
@patch('ona.tasks.OnaApiClient.get_form_definition')
class ProcessNewPackageScansTestCase(TestCase):
    def setUp(self):
        reset_bad_form_ids()

    def test_update_package_locations(self, mock_ona_form_def, mock_ona_form_submissions):
        self.assertFalse(FormSubmission.objects.all())
        # The test DATA fixture already contains the form def json
        submission = json.loads(PACKAGE_DATA)
        mock_ona_form_def.return_value = submission['form_definition']
        mock_ona_form_submissions.return_value = [submission]
        process_new_package_scans.run()
        self.assertEqual(1, FormSubmission.objects.count())
        # Only add the record once
        process_new_package_scans.run()
        self.assertEqual(1, FormSubmission.objects.count())

    def test_update_package_multiple_locations(self, mock_ona_form_def, mock_ona_form_submissions):
        PackageFactory(code=QR_CODE)
        self.assertFalse(FormSubmission.objects.all())
        # The test DATA fixture already contains the form def json
        submission = json.loads(PACKAGE_DATA)
        other_submission = deepcopy(submission)
        other_submission.update(
            _uuid="2a11435f-8eaf-44f9-bd75-00a4bac8fbce",
            current_location="STATUS_RECEIVED",
            _submission_time="2014-07-25T17:19:16",
        )
        mock_ona_form_def.return_value = submission['form_definition']
        mock_ona_form_submissions.return_value = [submission, other_submission]
        process_new_package_scans.run()
        self.assertEqual(2, FormSubmission.objects.count())
        loc = PackageScan.objects.all().order_by('when')[0]
        self.assertEqual(loc.status_label, 'English Zero_Point')
        self.assertEqual(loc.package.status, Shipment.STATUS_RECEIVED)
        self.assertEqual(loc.package.shipment.status, Shipment.STATUS_RECEIVED)
        loc = PackageScan.objects.all().order_by('when')[1]
        self.assertEqual(loc.status_label, 'English Received')
        self.assertEqual(loc.package.status, Shipment.STATUS_RECEIVED)
        self.assertEqual(loc.package.shipment.status, Shipment.STATUS_RECEIVED)

    @patch('ona.tasks.logger')
    def test_bad_form_id(self, mock_logger, mock_ona_form_def, mock_ona_form_submissions):
        mock_ona_form_def.return_value = None
        process_new_package_scans.run()
        self.assertIn(settings.ONA_PACKAGE_FORM_ID, bad_form_ids)
        self.assertTrue(mock_logger.error.called)


@override_settings(
    ONA_API_ACCESS_TOKEN='foo',
    ONA_DEVICEID_VERIFICATION_FORM_ID=111,
    ONA_PACKAGE_FORM_ID=123,
    ONA_DOMAIN='ona.io'
)
@patch('ona.tasks.OnaApiClient.get_form_definition', autospec=True)
@patch('ona.tasks.OnaApiClient.get_form_submissions', autospec=True)
class DeviceIdToUserTestCase(TestCase):

    def setUp(self):
        self.user = CtsUserFactory(code=QR_CODE)
        reset_bad_form_ids()

    def test_verify_deviceid(self, mock_ona_form_submissions, mock_get_form_definition):
        self.assertEqual('', self.user.deviceid)
        self.assertFalse(FormSubmission.objects.all())
        submission = json.loads(USER_CODE_DATA)
        mock_ona_form_submissions.return_value = [submission]
        verify_deviceid.run()
        self.assertEqual(1, FormSubmission.objects.count())
        # Passed minimum as the 'since' parm
        mock_ona_form_submissions.assert_called_with(ANY, 111, since=minimum_aware_datetime())
        # Only add the record once
        verify_deviceid.run()
        self.assertEqual(1, FormSubmission.objects.count())
        # passed the previous submission time as the 'since' parm when fetching forms
        subtime = OnaItemBase.parse_form_datetime(submission['_submission_time'])
        mock_ona_form_submissions.assert_called_with(ANY, 111, since=subtime)
        self.assertEqual('device_foo', CtsUser.objects.get(pk=self.user.pk).deviceid)

    def test_update_deviceid(self, mock_ona_form_submissions, mock_get_form_definition):
        # A later scan can update the user/device connection
        user2 = CtsUserFactory(code='test2', deviceid='device_foo')
        user3 = CtsUserFactory(code='test3', deviceid='device_foo')
        submission = json.loads(USER_CODE_DATA)
        mock_ona_form_submissions.return_value = [submission]
        verify_deviceid.run()
        # "new" user now has device
        self.assertEqual('device_foo', CtsUser.objects.get(pk=self.user.pk).deviceid)
        # and previous users do not
        self.assertEqual('', CtsUser.objects.get(pk=user2.pk).deviceid)
        self.assertEqual('', CtsUser.objects.get(pk=user3.pk).deviceid)

    @patch('ona.tasks.logger')
    def test_verify_deviceid_invalid_code(self, mock_logger, mock_ona_form_submissions,
                                          mock_get_form_definition):
        self.assertFalse(FormSubmission.objects.all())
        # The test DATA fixture already contains the form def json
        submission = json.loads(USER_CODE_DATA)
        submission['qr_code'] = 'foobar'
        mock_ona_form_submissions.return_value = [submission]
        verify_deviceid.run()
        self.assertEqual(0, FormSubmission.objects.count())
        self.assertTrue(mock_logger.error.called)

    def test_not_retrieving_same_forms_repeatedly(self, mock_ona_form_submissions,
                                                  mock_get_form_definition):
        # The test DATA fixture already contains the form def json
        submission = json.loads(USER_CODE_DATA)
        mock_ona_form_submissions.return_value = [submission]
        verify_deviceid.run()
        self.assertEqual(1, FormSubmission.objects.count())

    @patch('ona.tasks.logger')
    def test_bad_form_id(self, mock_logger, mock_ona_form_submissions,
                         mock_get_form_definition):
        mock_get_form_definition.return_value = None
        verify_deviceid.run()
        self.assertIn(settings.ONA_DEVICEID_VERIFICATION_FORM_ID, bad_form_ids)
        self.assertTrue(mock_logger.error.called)
