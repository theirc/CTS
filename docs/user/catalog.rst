Catalog
======================

The CTS catalog represents physical items that are placed in package templates
called Kits.  The catalog itself is not a true inventory system, in that it is not
aware of stock levels. Rather, it allows for users to create the blueprints for the
content of packages to be shipped.

The catalog is accessible via the *Catalog* link in the primary navigation.

Catalog Item
------------

A catalog item is defined by the following fields:

* **Item Code** -- A CTS defined code to identify the item
* **Description** -- A title or short description for the item
* **Category** -- The category of the item (Antibiotics, for example)
* **Unit** -- The unit of measurement (*1 box of 12 20-foot rolls of bandage*, for example)
* **Donor** -- The associated Donor from the CTS entities
* **T1 Code** -- The associated T1 Donor Code from the CTS entities
* **Supplier** -- The provider that fulfilled this item
* **Local Currency Cost** -- The cost per unit in the local currency
* **USD Cost** -- The cost per unit in U.S. Dollars
* **Weight** -- The weight of a unit

When selecting a category during Catalog Item creation/editing, one can choose an
existing category via auto-completion or supply a new category name.

Kit
---

The catalog is the interface to define a **Kit** which is a package template. For example,
a user could define a *Winter Kit* and add catalog items such as blankets, coats, etc.  Defining
this *Winter Kit* and its items does not in itself create packages for shipments.
It only provides the details of what items should be included in a Package that is based
off of a *Winter Kit*.

Catalog Listing
----------------

The catalog listing page allow for a number of basic interactions:

* **New Item** allows for creation of a new Catalog Item
* **Create Kit** allows for creation of a new Kit
* **Edit Catalog Item** clicking the pencil icon for a Catalog Item will allow for editing of the Catalog Item in a modal
* **Delete Catalog Item** clicking the **X** icon for a Catalog Item will allow for deletion of the Catalog Item
* **Select Kit** selects the current Kit that catalog items will be added to

Creating a **Kit** is straightforward:

#. Select *Create Kit* from the catalog list interface
#. Provice a short **name** and **description**
#. Press **Add Kit**

Once a **Kit** has been created (or selected from the list of  existing kits), additional functionalities
are exposed in the interface:

* **View Kit** renders the details about the current selected kit in a modal interface
* **Add Item to Kit** When you use the **'+'** button next to an item, the quantity you specify will be added to this kit.
* **Add All Items to Kit** Clicking the green **'+'** icon in the table header will add all Catalog Items with defined quantities to the selected **Kit**
* **Clear All Quantities** Clicking the **0** in the Quantity table header will reset all defined quantities to none.

