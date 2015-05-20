Users
======================

In order to access CTS, one must have a User account. Users are administered via the
Users link in the primary navigation. From this user listing, users can be added,
edited, or deleted.

* **Email Address** -- Unique identifier and username for site authentication
* **Name** -- The name of the user
* **Mobile** -- The mobile phone number that a user can be reached at
* **Skype** -- The Skype username for the user
* **Role** -- The role that the user possesses in the system
* **Colour** -- A color swatch associated with the user

All fields are editable except for *Code* and *Device ID*.

* A unique QR code is generated for the User when initially saved.
* The *Device ID* for a User is populated when a User scans their QR Code via a CTS provided phone.

Roles and Permissions
----------------------

CTS uses a number of user roles and associated permissions to ensure that
site users have the right level of access.

Coordinator
-----------

The IRC Coordinator is the administrator of the Supply Chain System. He/She is the only
user permitted to enter and view Referrer, Transporter and Receiver/End User data.
The Monitoring Manager reports to the Coordinator.

Monitoring Manager
------------------

The Monitoring Manager is a primary user of the system. The system is designed to
enable the Monitoring Manager to aid with the project's required monitoring and
reporting. The Monitoring Manager reports to the Coordinator.

*The monitoring manager's privileges are currently the same as the monitoring officer.*

Monitoring Officer
------------------

IRC Warehouse staff are typically assigned to the role of Monitor Officer. They  will create
and update a catalog of items, receive shipments ("stock in"), and create packages
that can be combined into shipments. This user reports to the Monitoring Manager.


Partner
-----------

Recipient  - These may be doctors, clinics, or service provision organizations
operating inside Syria and responding to the medical needs of conflict-affected
Syrians.


Create/Edit User
----------------

Users with the **Coordinator** role are able to create and edit other users. It is during
the create/edit process that a User can have their role assigned or changed.

#. Navigates to **/users/**
#. Click **New User** or the **Edit** pencil icon in the row of the User to edit
#. Add/Edit required fields
#. In the modal, choose an appropriate **Role** from the dropdown list
#. Click **Add/Save User** to save the User.

If a new user was created, the system will send the user an email with an
account activation link, similar to:

    You're receiving this email because a new account has been created for you at [server url].

    Please go to the following page and choose a new password:

    http://[server url]/reset/OTc/[3vn-6f7ca745c7e936513a0d]/

    Your email (remember for logging in later): [email address]

    Thanks for using our site!

    The [server url] team

When the recipient of the email clicks the activation link, they will be asked
to create and confirm a password for the new user account. Once saved, the user
can then login to the system.


Change Password
-----------------

A user may changed their password in one of two ways.

A logged in user can selected the  **Password** link in the menu to reset their password.

A user that has forgotten their login credentials can request instructions for resetting their
password from the login form via the *Forgotten your password?* link. The user must supply the
email associated with the account and the system will send them instructions as to how to reset
the password.


