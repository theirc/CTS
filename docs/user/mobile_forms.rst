Mobile Forms
======================

CTS makes heavy use of form submissions from mobile devices. One requirement for
these mobile devices is that they must support form submissions while the phone
has no connectivity. To fulfill this requirement CTS utilizes  `Ona <https://ona.io/>`_
and  `ODK Collect <http://opendatakit.org/use/collect/>`_.

Please familiarize yourself with the ODK Collect documentation before proceeding.

Configure ODK Collect
---------------------

In order to access the required CTS Forms, you will need to configure ODK Collect on the
mobile device.

#. Open ODK Collect on the device
#. Press the *Menu* button on the device
#. Select *General Settings*
#. Update the URL to **https://ona.rescue.org/[username]**
#. Press the *Back* button on the device
#. Press *Get Blank Form* in ODK Collect
#. Select all forms
#. Press *Get Selected*


Submit Form Data
-------------------

Once a device has forms on it, a user can open ODK Collect and fill out a blank instance
of a form.

#. Select *Fill Blank Form*
#. Choose a form
#. Fill out the form
#. Mark the form as finalized
#. Press *Save Form and Exit*


Upload Form Data
-------------------

ODK Collect stores completed form submissions on the device. ODK Collect can  be configured
to automatically upload stored form submissions when the  device is conected to wifi.

If automatic uploadi is not configured, you must manually upload the completed forms.

#. Select *Send Finalized Form*
#. Select the form instance(s) to upload
#. Press *Send Selected*
#. You will be informed of upload successes and failures


User Device Capture Form
-------------------------

The User Device Capture Form is a very simple form. It has one form input that requires
scanning a QR code associated with a :doc:`CTS User <users>`. The QR code can be found by navigating to the list
of Users and clicking the QR code icon. This will open the unique user QR code in a new browser tab/window.

The web application polls Ona for new form submissions and updates a user's deviceid as needed.


Package Delivery Form
----------------------

The Package Delivery Form allows CTS and Partner personnel to  update information related to a shipment
and its packages during the lifecycle of the shipment. The Package Delivery From is much more complex
than the User Device Capture Form:

* **Governate** -- Select the current administrative division
* **District** -- Select the current district
* **Sub-District** -- Select the current sub-district
* **Community** -- Supply the current community
* **P-code** -- If known, supply the current GPS precision code
* **Current Location** -- Select the Shipment's current location
* **Record Current Location** -- Record the current GPS coordinates
* **Number of Packages** -- Supply the number of packages to scan
* **Package Information** -- Scan the QR code for each package
* **Shipment Complete** -- Mark if the Shipment is complete
* **Shipment Inomplete Reason** -- Supply the reason the Shipment is incomplete


