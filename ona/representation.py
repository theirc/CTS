import json
import pytz

from datetime import datetime


class OnaItemBase(object):
    """Wrapper for an arbitrary Ona item derived from a JSON object.

    All keys from the JSON object are available as attributes on the class.
    If a value needs extra processing, you should create a property of the
    class with the same name to perform the processing. You may also create
    arbitrary properties and methods.
    """
    _date_attrs = ['_submission_time', ]
    _date_format = '%Y-%m-%dT%H:%M:%S'
    _settable_attrs = ['json']

    @classmethod
    def parse_form_datetime(cls, value):
        if '-' not in value[-6:]:
            value = datetime.strptime(value, cls._date_format).replace(tzinfo=pytz.UTC)
        return value

    def __init__(self, json):
        if not isinstance(json, dict):
            raise ValueError("Expected JSON data to be a dictionary; instead "
                             "it is {0}".format(type(json)))
        try:
            self.json = json
        finally:
            self.__initialized = True

    def __dir__(self):
        return sorted(set(dir(type(self)) + list(self.json.keys())))

    def __getattr__(self, attr):
        if attr in self.json:
            value = self.json.get(attr)
            if attr in self._date_attrs and value is not None:
                value = self.parse_form_datetime(value)
            return value
        raise AttributeError(attr)

    def __setattr__(self, attr, value):
        """
        It is unclear what the expected behavior of setting an an
        attribute on an item should be. Better than guess, users should be
        forced to either make a copy of the item from the new JSON data or
        explicitly update the underlying JSON data.
        """

        if attr != '_OnaItemBase__initialized' and attr not in self._settable_attrs:
            raise TypeError("Cannot edit an Ona item directly. Instead, "
                            "you should use `item.json['name'] = value`.")
        return super(OnaItemBase, self).__setattr__(attr, value)


class PackageScanFormSubmission(OnaItemBase):

    def get_gps_data(self, index):
        """Safely retrieve the element from the list, or a sane default (None)"""
        if hasattr(self, 'gps'):
            gps = self.gps.split(' ')
            try:
                return float(gps[index])
            except IndexError:
                return None

    def get_lat(self):
        """Return lat"""
        return self.get_gps_data(0)

    def get_lng(self):
        """Return lng"""
        return self.get_gps_data(1)

    def get_altitude(self):
        """Return altitude"""
        return self.get_gps_data(2)

    def get_accuracy(self):
        """Return accuracy"""
        return self.get_gps_data(3)

    def get_qr_codes(self):
        """Return a unique set of package qr codes"""
        key = 'package/qr_code'
        return set([x[key] for x in json.loads(self.package) if key in x])

    def get_current_packagescan_label(self):
        """
        Inspect the form definition and return the associated label for the
        current location value.
        """
        # Return the human readable version of the status
        # Values should look similar to the following samples, defined by the Ona XLSFOrm:
        # STATUS_IN_TRANSIT-Zero_Point
        # STATUS_IN_TRANSIT-Partner_Warehouse
        # STATUS_IN_TRANSIT-Pre-Distribution_Point
        # STATUS_RECEIVED-Distribution Point
        # STATUS_RECEIVED-Post-Distribution Point
        # Look up the suffix if available, else the prefix and return the appropriate label
        parts = self.current_location.split('-', 1)
        choices = json.loads(self.form_definition)['choices']['location_list']
        if len(parts) == 2:
            key = parts[1]
        else:
            key = parts[0]
        try:
            choice = [element for element in choices if key in element['name']][0]
            return choice['label']['English']
        except (IndexError, KeyError):
            return ''
