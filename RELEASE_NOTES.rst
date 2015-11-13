Release Notes for CTS
=====================

0.6.0 on Nov. 13, 2015
----------------------

* Speed up maps (#17)
* Use django-extensions to setup DB connection (#18)
* Log to syslog (#19)
* Update SECRET_KEY from environment (#22)

0.5.5 on Aug. 25, 2015
----------------------

* Improve error handling a bit when accessing ONA (#13)
* Fix Travis badge on Github (#14, thanks @stbenjam!)
* Update to Django 1.7.10; latest Django security release (#16)

0.5.4 on Jun. 10, 2015
----------------------

* Add /health/ URL for load balancers to use

0.5.3 on Jun. 9, 2015
---------------------

* Handle more places we could get a 404 retrieving Ona forms (#11)
* Better reporting when an Ona form ID doesn't work (#10)
* Fix bug viewing shipment package list for partners (#7)
* Don't store celery task results (#6)
* Break out deploy-related files to their own repo,
  https://github.com/theirc/CTS-ircdeploy
* Update and improve organization of documentation.
* Remove files related to migrating from CTS v2.

NEW REPO!  https://github.com/theirc/CTS-project

0.5.2 on Apr. 28, 2015
----------------------

* Point production at master
* Add migration to set country in package scans

0.5.1 on Apr. 14, 2015
----------------------

* Add migrations to eliminate duplicate package scan records
* Add partial DB index to prevent duplicate package scan records

0.5.0 on Mar. 24, 2015
----------------------

* Enable swap on EC2 instances upon boot
* Load packages table asynchronously for performance
* Compress javascript and CSS
* Compress package items ajax view
* Use a faster query for shipments on the shipment detail page

0.4.2 on Dec. 17, 2014
----------------------

* Fix for allowing postgres access from the readonly users'
  IP addresses.

0.4.1 on Dec. 17, 2014
----------------------

* Add readonly DB user (#424, #426)
* Set default from email address (should help with emails
  going to spam folder) (#423)

0.4.0 on Dec. 10, 2014
----------------------

* Document and clean up backup process

0.3.9 on Dec. 9, 2014
---------------------

* Give write perms on scans to officers

0.3.8 on Dec. 9, 2014
---------------------

* Add permissions for PackageScan model

0.3.7 on Dec. 9, 2014
---------------------

* Fix bug in package API (#421)
* Put a FROM address on server emails

0.3.6 on Nov. 21, 2014
----------------------

* More fixes for database/media backup

0.3.5 on Nov. 21, 2014
----------------------

* Fixes for database/media backup

0.3.4 on Nov. 20, 2014
----------------------

* Fix v2 to v3 data migration that transposed latitude and longitude on scan (#410)
* Fix map centering on rerender (#409)
* Infrastructure: Added database backups


0.3.3 on Nov. 17, 2014
----------------------

* Fix bug raising OnaApiClientException (#407)
* Fix reassigning devices to different users (#403)
* Fix maps zooming too deep (#400, #397)
* Fix intermittent test failures (#402)
* Fix misaligned totals on shipment details printout (#391)

0.3.2 on Nov. 6, 2014
---------------------

* Display something for shipment and package names on barcode printout (#395)
* Sort shipments by date initially (#394)
* Speed up shipment deleting (should make it work again) (#393)
* Remove last scan label from shipment status displays (#392)
* Make weight optional (#390)
* Allow device transfers from one user to another (#389)
* Fix deleting kits (#384)
* Fix bugs creating packages from kits (#385)

0.3.1 on Nov. 5, 2014
---------------------

* Allow different QR code sizes and different labels when printing barcodes (#383)
* Improve migration script (was running out of memory)
* Handle duplicate email when creating or editing users (#382)
* Support differnet Ona credentials per instance (#381)

0.3.0 on Nov. 3, 2014
---------------------

* Let coordinators change and reset user passwords (#379)
* Create new T1 and T3 on the fly when creating or editing donor (#380)
* Fix 500 on catalog page related to categories (#377)
* Give a more specific error message on failure to connect to Ona server (#378)
* Make Print popup go away more easily (#372)
* Rename the Location model to PackageScan (#374)

0.2.1 on October 30, 2014
-------------------------

* Fix div-by-zero in migration (#375)

0.2.0 on October 30, 2014
-------------------------

* Better input validation when adding items to kits (#352)
* Show percentage of packages for some statuses (#360)
* Add shipments to item report (#371)
* Allow scans that have no GPS data (#373)
* Better error logging when Ona form not found (#345)
* 3 decimal places for USD currency (#357)
* Create multiple packages at once (#361)
* Upgrade to Django 1.7.1 (#366)
* More unit tests (#368)
* Fix deleting users (#369)
* Improve package selection on shipment page (#358)
* Performance improvements when adding many packages (#362)
* Fix bulk package editing (#365)
* Process device captures more frequently (#356)
* Handle invalid user QR codes better (#351)
* Don't keep retrieving submitted device forms we've already seen (#351)
* Email the development team when servers have errors (#347)
* Fix totals line on shipment details printed page (#344)
* Fix div-by-zero in migration (#349)
* Filter ordering on package report (#338)
* Filter partner and shipment options based on donor and/or partner selection (#336)
* Partner permissions for reports (#319)
* Add quantity fields when creating packages from kits (#339)
* Monthly summary report (#342, #328)
* Shipment summary report (#341, #330)
* Better error on catalog import of non-Excel file (#343, #333)
* Fix 500 on bulk item editing (#340)
* Received items summary report (#329, #337)
* Remove donor filter for partner viewer (#336, #326)
* Fix content type on CSV downloads (#335)
* Fix partner filtering on package report (#334)
* Tests for reports (#314)
* Download reports as CSV (#317, #320)
* Packages not scanned inside syria report (#331)
* Fix kit editing (#324)
* Description not required for kits or packages (#325)
* Fix create shipment button not showing up (#332)
* Fix text on edit package details modal (#323)
* Change status filter to checkboxes (#331)
* Quote local currency in downloads (#320, #317)
* User docs (#264, #309)
* Fix filtering item report by partner (#321)
* Wrong label on shipment report (#322)
* Fix verbose names onSQL view models (#322)
* Alphabetize filters where appropriate (#316)
* Optimize reports (#255, #304)
* Quote exported values in salt (#311)
* Maps upgrades (#310)
* Only download new package scan form submissions (#305)
* Fix getting location list from form definition (#303)
* Add env and instance to page titles (#298)
* Add instructions for downloading data to the README (#300)
* Fixes for form tasks and better logging (#299)
* Add all quantities to kit (#166)
* Clear all quantities (#165)
* Doc links (#296)
* Less verbose doc production (#296)
* Device ID binding (#295, #290)
* Fix warning when salt creates postgres databases (#285)
* Totals on shipment view (#294)
* Admin docs (#293)
* Style table footer like header (#294)
* Salt fixes (#285)
* Instance specific migrations (#274)
* Remove currency name from model documentation fields (#274)
* Install git earlier (#291)
* Fab commands to dump and restore databases (#289)

0.1.0 on September 23, 2014
---------------------------

* New hostnames cts-staging.rescue.org, cts.rescue.org (#287)

0.0.9 on September 23, 2014
---------------------------

* Update shipment status from scan location (#273, #188)
* Restart servers on deploy (#284)
* Ona times are in UTC (#270, #286)
* Root URL path was 403 (#281)
* Migration fixes (#282)
* Do not display supplier details to partners (#271)
* Upgrade django-celery for Django 1.7 compatibility (#283)
* Multiple instances on one domain by URL path (#280)
* Map refactor (#279)
* Fix permissions for coordinators (#278, #277, #275, #276)
* Don't check local settings file for PEP-8 (#272)

0.0.8 on September 16, 2014
---------------------------

* Django 1.7 (#260)
* Fix donor migration bugs (#269)
* Serve docs on site (#267)
* Get vagrant test environment working (#266)
* Deploy SSL cert and key from secrets file (#265)
* Limit shipment views for partners (#261)
* Fix PostGIS setup (#250)
* Add OSM and ESRI test map layers (#259)
* Fix kit creation (#241, #257)

0.0.7 on August 29, 2014
------------------------

* Fix mismatched status displayed on shipments list and detail pages (#238, #245)
* Fix misalignment of create shipment and map view buttons (#254)
* Improve map page load performance (#253, #251)
* Improve shipments page load performance (#249)
* List partners by name instead of email (#252)
* Re-order map filters and remove supplier filter (#248)
* Add reports by location (#231, #239)
* Fix migrations for Turkey data (#247)
* Migrate users from v2 (#235)
* Login by email instead of username, store user name in single field (to match v2) (#237)
* Set local currencies on instances (#240)
* Implement partners as users instead of a separate table (#236)
* Set up Iraq site (#233)

0.0.6 on August 25, 2014
------------------------

* Fix exception when editing bulk package items (#228)
* When editing details of existing package, button shouldn't say "Save New Package" (#230)
* Save and Print buttons misaligned (#229)
* Add headers on shipment page (#232)
* Make entire row clickable on packages table on shipment page (#232)
* Highlight row of selected package (#232)
* Add help on create package from kit modal (#232)
* Start on sysadmin docs (#227)

0.0.5 on August 21, 2014
------------------------

* Django 1.6.6 - security upgrade (#223)
* More New Relic support (#226)

0.0.4 on August 20, 2014
------------------------

* New Relic support (#98)
* Deploy for Jordan and Turkey (#3)
* Map package routes (#217)
* Ona support
* User password management (assign initial; reset) (#176)
* Fix sorting shipments by date (#218)
* Fix "More Actions" button on shipments page (#216)
* Update shipments list columns per feedback (#215)

0.0.3 on August 14, 2014
------------------------

* Start adding configuration for Jordan and Turkey instances
* Finish up catalog pages
* Finish up shipments pages
* Add entities section (donors, suppliers, transporters, users, partners)
* Start on reports pages
* Read-only REST API
* Roles and permissions

0.0.2 on August 1, 2014
-----------------------

* Remove pagination from tables
* Better error indication when quantity is negative
* Package status
* Shipment actions
* Shipment details page
* Summary manifest page
* Message when user changes selected kit
* Add location data
* Make links in tables green
* Remove borders from tables
* Better formatting of import errors
* Fix styling on select controls
* Make some modals larger
* Styling updates to better match comps
* Many misc. bug fixes

0.0.1 on July 15, 2014
----------------------

* Initial "release"
* Most of catalog page working.
* Shipments and packages partially implemented.
* Entities and users can be created and edited. Open bug about
  Donor T1 codes.
* Various style issues need to be fixed.
