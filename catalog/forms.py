import selectable.forms as selectable

from django import forms
from django.forms.widgets import HiddenInput

from catalog.lookups import T1DonorCodeLookup, T3DonorCodeLookup, ItemCategoryLookup
from catalog.models import CatalogItem, ItemCategory, Donor, DonorCode, Supplier
from shipments.models import Kit, KitItem


CATALOG_ITEM_FIELDS = [
    'item_code',
    'description',
    'unit',
    'price_usd',
    'price_local',
    'item_category',
    'donor',
    'donor_t1',
    'supplier',
    'weight',
]

KIT_FIELDS = [
    'name',
    'description',
]

# Limit how many of an item they can add to a kit at one time.
# This is arbitrary.  The quantity field on the kit items can
# have a value up to 2 billion, so we could make this quite a bit
# larger. We just don't want to set it to 2 billion and have them
# add that twice and blow the field value limit.
MAX_QUANTITY = 50000000


class CatalogItemEditForm(forms.ModelForm):
    item_category = forms.CharField(
        label='Begin typing to select an existing or add a new category.',
        widget=selectable.AutoComboboxWidget(ItemCategoryLookup, allow_new=True),
        required=True,
    )

    class Meta:
        model = CatalogItem
        fields = CATALOG_ITEM_FIELDS

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        if 'weight' not in kwargs['initial']:
            kwargs['initial']['weight'] = ''
        super(CatalogItemEditForm, self).__init__(*args, **kwargs)

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight == '':
            weight = None
        return weight

    def clean_item_category(self):
        name = self.cleaned_data.get('item_category')
        if name:
            category = ItemCategory.objects.filter(name__iexact=name).first()
            if not category:
                category = ItemCategory.objects.create(name=name)
            return category


class CatalogFileImportForm(forms.Form):
    file = forms.FileField()


class CatalogItemImportForm(forms.ModelForm):
    """
    Validate values on a row of data being imported into the catalog.
    """

    # Override the foreign key fields so we can look them up by name.
    # (If we used ModelChoiceFields, the input values would be expected
    # to be the primary keys, but we want to use the names.)
    item_category = forms.CharField(required=True)
    donor = forms.CharField(required=False)
    donor_t1 = forms.CharField(required=False)
    supplier = forms.CharField(required=False)

    class Meta:
        model = CatalogItem
        fields = [
            'item_code', 'description', 'unit', 'price_usd', 'price_local',
            'item_category', 'donor', 'donor_t1', 'supplier', 'weight',
        ]

    def _excise_trailing_zero(self, value):
        """This forms processes xlrd data, which reads in XLS data. A cell with
        a perceived INT will be imported as a FLOAT.

        Utilize this method to excise the trailing '.0'
        """
        return value.rstrip('.0')

    def clean_item_category(self):
        name = self.cleaned_data.get('item_category')
        if name:
            name = self._excise_trailing_zero(name)
            obj, created = ItemCategory.objects.get_or_create(name=name)
            return obj

    def clean_supplier(self):
        name = self.cleaned_data.get('supplier')
        if name:
            name = self._excise_trailing_zero(name)
            obj, created = Supplier.objects.get_or_create(name=name)
            return obj

    def clean_donor(self):
        name = self.cleaned_data.get('donor')
        if name:
            name = self._excise_trailing_zero(name)
            obj, created = Donor.objects.get_or_create(name=name)
            return obj

    def clean_donor_t1(self):
        code = self.cleaned_data.get('donor_t1')
        if code:
            code = self._excise_trailing_zero(code)
            obj, created = DonorCode.objects.get_or_create(
                code=code, donor_code_type=DonorCode.T1
            )
            return obj

    def save(self, *args, **kwargs):
        item = super(CatalogItemImportForm, self).save(*args, **kwargs)
        if (item.donor and item.donor_t1) and item.donor_t1 not in item.donor.t1_codes.all():
            item.donor.t1_codes.add(item.donor_t1)
        return item


class DonorEditForm(forms.ModelForm):
    new_t1_codes = forms.CharField(max_length=60, required=False,
                                   label="New T1 codes (comma-separated)")
    new_t3_codes = forms.CharField(max_length=60, required=False,
                                   label="New T3 codes (comma-separated)")

    class Meta:
        model = Donor
        fields = [
            'name', 't1_codes', 't3_codes',
            'new_t1_codes', 'new_t3_codes'
        ]
        widgets = {
            't1_codes': selectable.AutoComboboxSelectMultipleWidget(
                lookup_class=T1DonorCodeLookup,
            ),
            't3_codes': selectable.AutoComboboxSelectMultipleWidget(
                lookup_class=T3DonorCodeLookup,
            ),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        for field in ['new_t1_codes', 'new_t3_codes']:
            if field not in kwargs['initial']:
                kwargs['initial'][field] = ''
        super(DonorEditForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        for new_codes_field_name, code_type, codes_field_name in [
            ('new_t1_codes', DonorCode.T1, 't1_codes'),
            ('new_t3_codes', DonorCode.T3, 't3_codes')
        ]:
            new_codes = self.cleaned_data.pop(new_codes_field_name)
            if new_codes:
                # self.cleaned_data['t1_codes'] is a queryset, not a simple list
                selected_pks = list(self.cleaned_data[codes_field_name].
                                    values_list('pk', flat=True))
                new_codes = [x.strip() for x in new_codes.split(',')]
                for name in new_codes:
                    code, unused = DonorCode.objects.get_or_create(
                        code__iexact=name,
                        donor_code_type=code_type,
                        defaults=dict(code=name))
                    selected_pks.append(code.pk)
                self.cleaned_data[codes_field_name] = DonorCode.objects.filter(pk__in=selected_pks)
        return super(DonorEditForm, self).save(*args, **kwargs)


class KitEditForm(forms.ModelForm):
    class Meta:
        model = Kit
        fields = KIT_FIELDS

    def __init__(self, **kwargs):
        super(KitEditForm, self).__init__(**kwargs)
        # Add a form field to change the quantity in each kit item
        if self.instance:
            kit = self.instance
            for item in kit.items.all():
                field_name = 'quantity_%d' % item.pk
                self.fields[field_name] = forms.IntegerField()
                self.initial[field_name] = item.quantity

    def save(self, *args, **kwargs):
        kit = super(KitEditForm, self).save(*args, **kwargs)
        for field_name in self.fields:
            if field_name.startswith('quantity_'):
                item_pk = int(field_name[-(len(field_name) - len('quantity_')):])
                try:
                    item = KitItem.objects.get(pk=item_pk)
                    new_quantity = self.cleaned_data[field_name]
                    if new_quantity == 0:
                        item.delete()
                    elif item.quantity != new_quantity:
                        item.quantity = new_quantity
                        item.save()
                except KitItem.DoesNotExist:
                    pass  # not much we can do
        return kit


class AddKitItemsForm(forms.Form):
    selected_kit = forms.ModelChoiceField(
        queryset=Kit.objects.all(),
        widget=HiddenInput
    )

    def __init__(self, *args, **kwargs):
        super(AddKitItemsForm, self).__init__(*args, **kwargs)
        # Add a field for each catalog item
        for item in CatalogItem.objects.all():
            field_name = 'quantity-%d' % item.pk
            field = forms.IntegerField(max_value=MAX_QUANTITY, min_value=0, required=False)
            field.item_pk = item.pk
            self.fields[field_name] = field
