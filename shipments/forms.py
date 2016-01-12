from datetime import timedelta

import selectable.forms as selectable

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import CheckboxSelectMultiple
from django.forms.extras import SelectDateWidget
from django.utils.translation import ugettext_lazy as _

from catalog.lookups import CatalogItemLookup
from cts.utils import uniqid, is_int
from shipments.models import Shipment, Package, Kit, PackageItem


SHIPMENT_FIELDS = [
    'description',
    'shipment_date',
    'store_release',
    'date_in_transit',
    'date_picked_up',
    'estimated_delivery',
    'date_received',
    'transporter',
    'partner',
    'acceptable',
    'status_note',
    ]


class ShipmentEditForm(forms.ModelForm):
    estimated_delivery = forms.IntegerField(
        label=_("Est. delivery (in days)"),
        min_value=0,
        max_value=999,
        initial=0
    )
    description = forms.CharField(
        required=False,
        initial=''
    )
    shipment_date = forms.DateField(widget=SelectDateWidget)

    class Meta:
        model = Shipment
        fields = SHIPMENT_FIELDS

    def __init__(self, *args, **kwargs):
        super(ShipmentEditForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.fields['description'].widget.attrs['placeholder'] = kwargs['instance']
        if getattr(self.instance, 'pk', None):
            if self.instance.date_expected and self.instance.shipment_date:
                estimated_duration = self.instance.date_expected - self.instance.shipment_date
                self.initial['estimated_delivery'] = estimated_duration.days

    def clean(self):
        data = self.cleaned_data
        if 'estimated_delivery' in data and data.get('shipment_date', False):
            data['date_expected'] = (data['shipment_date'] +
                                     timedelta(days=data['estimated_delivery']))
        return data

    def save(self, *args, **kwargs):
        # date_expected is not exposed as a field so we have to set it ourselves
        self.instance.date_expected = self.cleaned_data.get('date_expected', None)
        return super(ShipmentEditForm, self).save(*args, **kwargs)


class ShipmentLostForm(forms.Form):
    acceptable = forms.ChoiceField(
        choices=[
            (True, 'Yes'),
            (False, 'No'),
        ]
    )
    notes = forms.CharField(
        widget=forms.TextInput,
    )


PACKAGE_FIELDS = [
    'name',
    'description',
]

NEW_PACKAGE_FROM_KIT_FIELDS = \
    ['package_quantity'] + PACKAGE_FIELDS


def create_packages_and_items(shipment, name, description, num_packages, number_of_each_kit):
    """

    :param shipment: Shipment to add the packages to.
    :param name: Name to use for every package.
    :param description: Description to use for every package.
    :param num_packages: How many packages to create
    :param number_of_each_kit: A dictionary, key is a Kit, value is the number of copies of
    the kit to add to each package.
    :return: QuerySet of the packages that were created.
    """
    first_pkg_number = shipment.next_package_number_in_shipment()
    kits = number_of_each_kit.keys()
    if len(kits) == 1:
        only_kit = kits[0]
    else:
        only_kit = None

    Package.objects.bulk_create([
        Package(shipment=shipment,
                name=name,
                description=description,
                kit=only_kit,
                number_in_shipment=i + first_pkg_number,
                code='%s%d.%d' % (settings.PREFIX_URL, shipment.id, i + first_pkg_number))
        for i in range(num_packages)
    ])

    # We don't know what PKs were assigned to our new packages, so we
    # need to query for the created packages. It's just one query, though.
    packages_created = shipment.packages.filter(number_in_shipment__gte=first_pkg_number)

    if number_of_each_kit:
        # Go ahead and create package items from kits in each package
        PackageItem.objects.bulk_create([
            PackageItem.from_kit_item(package, kit_item,
                                      quantity=number_of_each_kit[kit] * kit_item.quantity,
                                      save=False)
            for package in packages_created
            for kit in kits
            for kit_item in kit.items.all()
        ])
    return packages_created


class PackageCreateForm(forms.ModelForm):
    package_quantity = forms.IntegerField(
        label="Number of packages to create",
    )

    def __init__(self, *args, **kwargs):
        self.shipment = kwargs.pop('shipment', None)
        super(PackageCreateForm, self).__init__(*args, **kwargs)
        if self.instance.shipment_id is None:
            self.instance.shipment = self.shipment
        if not self.instance.code:
            self.instance.code = uniqid()

    def save(self, *args, **kwargs):
        """
        :return: QuerySet of the packages that were created.
        """
        return create_packages_and_items(self.shipment, self.cleaned_data['name'],
                                         self.cleaned_data['description'],
                                         self.cleaned_data['package_quantity'], {})

    class Meta(object):
        model = Package
        fields = PACKAGE_FIELDS + ['package_quantity']


class PackageEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.shipment = kwargs.pop('shipment', None)
        super(PackageEditForm, self).__init__(*args, **kwargs)
        if self.instance.shipment_id is None:
            self.instance.shipment = self.shipment
        if not self.instance.code:
            self.instance.code = uniqid()

    class Meta(object):
        model = Package
        fields = PACKAGE_FIELDS


class NewPackageFromKitForm(forms.ModelForm):
    package_quantity = forms.IntegerField(
        label="Number of packages to create"
    )

    class Meta(object):
        model = Package
        fields = NEW_PACKAGE_FROM_KIT_FIELDS

    def __init__(self, *args, **kwargs):
        if 'shipment' not in kwargs:
            raise ValueError("Must pass 'shipment' to NewPackageFromKitForm")
        self.shipment = kwargs.pop('shipment')
        super(NewPackageFromKitForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['description'].required = False
        if not self.instance.code:
            self.instance.code = uniqid()

    def clean(self):
        # Get kit quantities from the data that was passed in
        name_prefix = "kit-quantity-"
        prefix_len = len(name_prefix)

        kits = {
            Kit.objects.get(pk=int(name[prefix_len:])): int(value)
            for name, value in self.data.iteritems()
            if name.startswith(name_prefix) and value and is_int(value) and int(value)
        }
        self.cleaned_data['kits'] = kits

        if len(kits) == 0:
            raise ValidationError('Please add a quantity of at least one kit')

        if len(kits) > 1:
            if not self.cleaned_data.get('name', False):
                raise ValidationError('Name required if more than one '
                                      'kit is included')
        # If there's just one kit, default the name and description to its name and description
        if len(kits) == 1:
            kit = kits.keys()[0]
            if not self.cleaned_data.get('name', False):
                self.cleaned_data['name'] = kit.name
            if not self.cleaned_data.get('description', False):
                self.cleaned_data['description'] = kit.description
        return self.cleaned_data

    def save(self, *args, **kwargs):
        """
        :return: QuerySet of the packages that were created.
        """
        return create_packages_and_items(self.shipment,
                                         self.cleaned_data['name'],
                                         self.cleaned_data['description'],
                                         self.cleaned_data['package_quantity'],
                                         number_of_each_kit=self.cleaned_data['kits'],
                                         )


PACKAGE_ITEM_FIELDS = [
    'description',
    'unit',
    'price_usd',
    'price_local',
    'item_category',
    'donor',
    'donor_t1',
    'supplier',
    'weight',
    'quantity',
]

PACKAGE_ITEM_BULK_EDIT_FIELDS = [
    'item_category',
    'donor',
    'donor_t1',
    'supplier',
]


class PackageItemEditForm(forms.ModelForm):

    class Meta(object):
        model = PackageItem
        fields = PACKAGE_ITEM_FIELDS


class PackageItemBulkEditForm(forms.ModelForm):
    class Meta(object):
        model = PackageItem
        fields = PACKAGE_ITEM_BULK_EDIT_FIELDS

    def __init__(self, *args, **kwargs):
        super(PackageItemBulkEditForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class PackageItemCreateForm(forms.Form):
    catalog_item = selectable.AutoCompleteSelectField(
        lookup_class=CatalogItemLookup,
        label="Begin typing to select a catalog item.",
        widget=selectable.AutoComboboxSelectWidget,
        required=True)
    quantity = forms.IntegerField(initial=1, required=True, min_value=1)

    def __init__(self, package, *args, **kwargs):
        self.package = package
        super(PackageItemCreateForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        catalog_item = self.cleaned_data['catalog_item']
        quantity = self.cleaned_data['quantity']
        return PackageItem.from_catalog_item(self.package, catalog_item, quantity)

PRINT_FORMAT_SUMMARY = 1
PRINT_FORMAT_FULL = 2
PRINT_FORMAT_DETAILS = 3
PRINT_FORMAT_CODES = 4
PRINT_FORMAT_CHOICES = [
    (PRINT_FORMAT_SUMMARY, "Summary manifests"),
    (PRINT_FORMAT_FULL, "Full manifests"),
    (PRINT_FORMAT_DETAILS, "Shipment details"),
    (PRINT_FORMAT_CODES, "Package barcodes"),
]
PRINT_FORMAT_DEFAULT = PRINT_FORMAT_SUMMARY


QRCODE_2 = 2
QRCODE_6 = 6
QRCODE_8 = 8
QRCODE_16 = 16
QRCODE_SIZE_CHOICES = [
    (QRCODE_2, "2x2cm"),
    (QRCODE_6, "6x6cm"),
    (QRCODE_8, "8x8cm"),
    (QRCODE_16, "16x16cm"),
]
QRCODE_DEFAULT_SIZE = QRCODE_6
QRCODE_FORMATS = [PRINT_FORMAT_FULL, PRINT_FORMAT_CODES]

LABEL_PACKAGE_NUMBER = 1
LABEL_PARTNER_NAME = 2
LABEL_PACKAGE_NAME = 3
LABEL_SHIPMENT_NAME = 4
LABEL_PACKAGE_CODE = 5
LABEL_CHOICES = [
    (LABEL_PACKAGE_NUMBER, "Package number"),
    (LABEL_PACKAGE_CODE, "Package code"),
    (LABEL_PARTNER_NAME, "Partner name"),
    (LABEL_PACKAGE_NAME, "Package name"),
    (LABEL_SHIPMENT_NAME, "Shipment name"),
]
LABEL_CHOICES_DEFAULT = [x for x, y in LABEL_CHOICES]  # ALL
LABEL_FORMATS = [PRINT_FORMAT_CODES]


class PrintForm(forms.Form):
    print_format = forms.TypedChoiceField(
        choices=PRINT_FORMAT_CHOICES,
        initial=PRINT_FORMAT_DEFAULT,
        coerce=int
    )
    qrcode_size = forms.TypedChoiceField(
        label="QR code size (approximate)",
        choices=QRCODE_SIZE_CHOICES,
        initial=QRCODE_DEFAULT_SIZE,
        coerce=int
    )
    labels = forms.MultipleChoiceField(
        label="Labels to print",
        choices=LABEL_CHOICES,
        initial=LABEL_CHOICES_DEFAULT,
        widget=CheckboxSelectMultiple
    )
