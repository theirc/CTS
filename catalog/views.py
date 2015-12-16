#
# CRUD for catalog items
#
import json
import logging
import os
import re
from tempfile import NamedTemporaryFile

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.forms import models as model_forms
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DeleteView, CreateView, FormView, View

from braces.views import PermissionRequiredMixin

from catalog.forms import CatalogFileImportForm, CatalogItemEditForm, DonorEditForm, \
    CATALOG_ITEM_FIELDS, KitEditForm, AddKitItemsForm
from catalog.models import CatalogItem, ItemCategory, Transporter, Supplier, \
    Donor, DonorCode
from catalog.utils import catalog_import, CatalogImportFailure, IMPORT_COLUMN_NAMES
from cts.utils import FormErrorReturns400Mixin, DeleteViewMixin
from shipments.models import Kit, KitItem


logger = logging.getLogger(__name__)

FIELD_NAME_RE = re.compile('^quantity-(\d+)$')


class CatalogItemCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    form_class = CatalogItemEditForm
    permission_required = 'catalog.add_catalogitem'
    model = CatalogItem
    success_url = reverse_lazy('catalog_list')
    template_name = 'catalog/catalogitem_new_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "New item added")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class CatalogItemListView(PermissionRequiredMixin, FormErrorReturns400Mixin, FormView):
    form_class = AddKitItemsForm
    permission_required = 'catalog.add_catalogitem'
    success_url = reverse_lazy('catalog_list')
    template_name = 'catalog/catalogitem_list.html'

    def get_queryset(self):
        queryset = CatalogItem.objects.all().prefetch_related('item_category')
        # DataTables is going to order them for us, so save that time on the query
        # (doesn't seem to matter)
        queryset = queryset.order_by()
        self.q = self.request.GET.get('q', '')
        if self.q:
            queryset = queryset.filter(description__icontains=self.q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(CatalogItemListView, self).get_context_data(**kwargs)
        context['object_list'] = self.get_queryset()
        context['q'] = self.q
        context['categories'] = ItemCategory.objects.all()
        form_class = model_forms.modelform_factory(CatalogItem, fields=CATALOG_ITEM_FIELDS)
        context['create_item_form'] = form_class()
        context['kits'] = Kit.objects.all()
        context['nav_catalog'] = True
        return context

    def form_valid(self, form):

        kit = form.cleaned_data['selected_kit']
        # Remove that field, now all that's left are item quantities to add
        del form.cleaned_data['selected_kit']

        # kit_pk = kit.pk
        msgs = set()  # gather messages and create all at once, without duplicates
        errors = False
        to_add = []  # list of tuples of (catalog item, quantity to add)
        for field_name, quantity in form.cleaned_data.iteritems():
            if quantity:
                m = FIELD_NAME_RE.match(field_name)
                item_pk = m.group(1)
                try:
                    catalog_item = CatalogItem.objects.get(pk=int(item_pk))
                except CatalogItem.DoesNotExist:
                    msgs.add("Invalid catalog item - might have been deleted since catalog page "
                             "was loaded.  Try again.")
                    errors = True
                    break
                to_add.append((catalog_item, quantity))
        if not errors:
            for catalog_item, quantity in to_add:
                resulting_quantity = add_item_to_kit(kit, catalog_item, quantity)
                if resulting_quantity > quantity:
                    msgs.add("Added %d more of %s; there are now %d." % (
                        quantity, catalog_item.description, resulting_quantity))
                else:
                    msgs.add("Added %d of %s." % (
                        quantity, catalog_item.description))
        messages.info(self.request, '\n'.join(msgs))
        return super(CatalogItemListView, self).form_valid(form)


class CatalogItemUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    form_class = CatalogItemEditForm
    permission_required = 'catalog.change_catalogitem'
    model = CatalogItem
    success_url = reverse_lazy('catalog_list')
    template_name = 'catalog/catalogitem_edit_modal.html'

    def get_initial(self):
        item_category = self.object.item_category
        return {'item_category': item_category, }

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class CatalogItemDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                            DeleteView):
    permission_required = 'catalog.delete_catalogitem'
    model = CatalogItem
    success_url = reverse_lazy('catalog_list')
    cancel_url = success_url


#
# Other catalog views
#

class CatalogImportView(PermissionRequiredMixin, FormErrorReturns400Mixin, FormView):
    form_class = CatalogFileImportForm
    permission_required = 'catalog.add_catalogitem'
    success_url = reverse_lazy('catalog_list')
    template_name = 'catalog/catalog_import_modal.html'

    def column_names(self):
        return IMPORT_COLUMN_NAMES

    def form_valid(self, form):
        f = self.request.FILES['file']
        path = None
        try:
            if hasattr(f, 'temporary_file_path'):
                # Django already saved the uploaded file to our disk
                path = f.temporary_file_path()
            else:
                # We need to save it ourselves
                tmpf = NamedTemporaryFile(mode='wb', delete=False)
                path = tmpf.name
                for chunk in f.chunks():
                    tmpf.write(chunk)
                tmpf.close()
            try:
                num_new = catalog_import(path)
            except CatalogImportFailure as e:

                error_msg = "Something went wrong importing the catalog, nothing was imported."
                for err in e.errlist:
                    error_msg = '%s\n %s' % (error_msg, err)
                form.errors['__all__'] = error_msg
                return self.form_invalid(form)

            messages.info(self.request, "Imported %d new item%s" %
                          (num_new, '' if num_new == 1 else 's'))
        finally:
            if path and os.path.exists(path):
                os.remove(path)
        return super(CatalogImportView, self).form_valid(form)


#
# CRUD-lite for Kits
#

class KitCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    form_class = KitEditForm
    permission_required = 'shipments.add_kit'
    model = Kit
    success_url = reverse_lazy('catalog_list')
    template_name = 'catalog/kit_new_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        result = {
            'kit_pk': self.object.pk,
            'name': self.object.name,
        }
        return HttpResponse(json.dumps(result), content_type='text/json')


class KitUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    form_class = KitEditForm
    permission_required = 'shipments.change_kit'
    model = Kit
    success_url = reverse_lazy('catalog_list')
    template_name = 'catalog/kit_edit_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        result = {
            'kit_pk': self.object.pk,
            'name': self.object.name,
        }
        return HttpResponse(json.dumps(result), content_type='text/json')


class KitDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                    DeleteView):
    permission_required = 'shipments.delete_kit'
    model = Kit
    success_url = reverse_lazy('catalog_list')
    cancel_url = success_url

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL.
        """
        kit = self.get_object()

        # Need to remove any references from Packages - we only store the
        # kit that was used to create the package for historical reasons anyway.
        kit.package_set.update(kit=None)

        return super(KitDeleteView, self).delete(request, *args, **kwargs)


def add_item_to_kit(kit, catalog_item, quantity):
    """
    Add some number of a particular catalog item to a kit,
    making sure we don't have more than one KitItem per
    CatalogItem.

    :param kit: Kit object
    :param catalog_item: CatalogItem object
    :param quantity: How many to add
    :return: Resulting number of this item in the Kit
    """

    # Before we do anything else, check if the Kit already has multiple KitItems
    # (more than 1) for this CatalogItem.  If so, we'll collapse them down to one
    # KitItem containing the total current quantity of this CatalogItem before
    # we continue.
    existing_items = KitItem.objects.filter(kit=kit, catalog_item=catalog_item)
    if existing_items.count() > 1:
        # Need to merge them
        item_to_keep = existing_items[0]
        items_to_merge = existing_items.exclude(pk=item_to_keep.pk)
        for old_item in items_to_merge:
            item_to_keep.quantity += old_item.quantity
        item_to_keep.save()
        items_to_merge.delete()
        existing_item = item_to_keep
    elif existing_items.count() == 1:
        existing_item = existing_items[0]
    else:
        existing_item = None

    if existing_item:
        existing_item.quantity += quantity
        existing_item.save()
    else:
        existing_item = KitItem.objects.create(
            kit=kit,
            catalog_item=catalog_item,
            quantity=quantity,
        )
    return existing_item.quantity


class KitAddItemView(PermissionRequiredMixin, FormErrorReturns400Mixin, View):
    permission_required = 'shipments.add_kititem'

    def post(self, request, kit_pk, item_pk, quantity, *args, **kwargs):
        """
        If successful, returns text message about it.
        """
        status = 200
        msgs = []

        # Use form to validate
        field_name = 'quantity-%d' % int(item_pk)
        form = AddKitItemsForm(
            data={
                'selected_kit': kit_pk,
                field_name: quantity
            }
        )
        if not form.is_valid():
            return HttpResponse(form.errors[field_name], status=400)

        kit = get_object_or_404(Kit, pk=int(kit_pk))
        catalog_item = get_object_or_404(CatalogItem, pk=int(item_pk))
        quantity = int(quantity)
        resulting_quantity = add_item_to_kit(kit, catalog_item, quantity)
        if resulting_quantity > quantity:
            msgs.append("Added %d more of item %s to kit %s." % (
                quantity, catalog_item.description, kit.name))
        else:
            msgs.append("Added %d of item %s to kit %s." % (
                quantity, catalog_item.description, kit.name))
        msgs.append("There are %d of item %s in kit %s." % (
                    resulting_quantity, catalog_item.description, kit.name))

        return HttpResponse('\n'.join(msgs), status=status)


class KitItemDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                        DeleteView):
    permission_required = 'shipments.delete_kititem'
    model = KitItem
    success_url = reverse_lazy('catalog_list')
    cancel_url = success_url


#
# CRUD for Transporter
#

class TransporterCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    permission_required = 'catalog.add_transporter'
    model = Transporter
    fields = ['name']
    success_url = reverse_lazy('transporter_list')
    template_name = 'catalog/transporter_new_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "New transporter added")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class TransporterListView(PermissionRequiredMixin, ListView):
    permission_required = 'catalog.add_transporter'
    model = Transporter
    fields = ['name']
    queryset = Transporter.objects.all()

    def get_context_data(self, **kwargs):
        context = super(TransporterListView, self).get_context_data(**kwargs)
        form_class = model_forms.modelform_factory(self.model, fields=self.fields)
        context['create_item_form'] = form_class()
        context['nav_entities'] = True
        context['subnav_transporters'] = True
        return context


class TransporterUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    permission_required = 'catalog.change_transporter'
    model = Transporter
    fields = ['name']
    success_url = reverse_lazy('transporter_list')
    template_name = 'catalog/transporter_edit_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class TransporterDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                            DeleteView):
    permission_required = 'catalog.delete_transporter'
    model = Transporter
    success_url = reverse_lazy('transporter_list')
    cancel_url = success_url


#
# CRUD for Supplier
#

class SupplierCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    permission_required = 'catalog.add_supplier'
    model = Supplier
    fields = ['name']
    success_url = reverse_lazy('supplier_list')
    template_name = 'catalog/supplier_new_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "New supplier added")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class SupplierListView(PermissionRequiredMixin, ListView):
    permission_required = 'catalog.add_supplier'
    model = Supplier
    fields = ['name']
    queryset = Supplier.objects.all()

    def get_context_data(self, **kwargs):
        context = super(SupplierListView, self).get_context_data(**kwargs)
        form_class = model_forms.modelform_factory(self.model, fields=self.fields)
        context['create_item_form'] = form_class()
        context['nav_entities'] = True
        context['subnav_suppliers'] = True
        return context


class SupplierUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    permission_required = 'catalog.change_supplier'
    model = Supplier
    fields = ['name']
    success_url = reverse_lazy('supplier_list')
    template_name = 'catalog/supplier_edit_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class SupplierDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                         DeleteView):
    permission_required = 'catalog.delete_supplier'
    model = Supplier
    success_url = reverse_lazy('supplier_list')
    cancel_url = success_url

    def dispatch(self, request, *args, **kwargs):
        supplier = self.get_object()
        if not supplier.is_deletable():
            messages.error(request,
                           "You may not delete supplier {} after packages have shipped."
                           .format(supplier.name))
            return redirect(self.cancel_url)
        return super(SupplierDeleteView, self).dispatch(request, *args, **kwargs)


#
# CRUD for Category
#

class CategoryCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    permission_required = 'catalog.add_itemcategory'
    model = ItemCategory
    fields = ['name']
    success_url = reverse_lazy('category_list')
    template_name = 'catalog/category_new_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "New category added")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class CategoryListView(PermissionRequiredMixin, ListView):
    permission_required = 'catalog.add_itemcategory'
    model = ItemCategory
    fields = ['name']
    queryset = ItemCategory.objects.all()
    template_name = 'catalog/category_list.html'

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        form_class = model_forms.modelform_factory(self.model, fields=self.fields)
        context['create_item_form'] = form_class()
        context['nav_entities'] = True
        context['subnav_categories'] = True
        return context


class CategoryUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    permission_required = 'catalog.change_itemcategory'
    model = ItemCategory
    fields = ['name']
    success_url = reverse_lazy('category_list')
    template_name = 'catalog/category_edit_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class CategoryDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                         DeleteView):
    permission_required = 'catalog.delete_itemcategory'
    model = ItemCategory
    success_url = reverse_lazy('category_list')
    cancel_url = success_url


#
# CRUD for Donor
#

class DonorCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    form_class = DonorEditForm
    permission_required = 'catalog.add_donor'
    model = Donor
    success_url = reverse_lazy('donor_list')
    template_name = 'catalog/donor_new_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "New donor added")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class DonorListView(PermissionRequiredMixin, ListView):
    permission_required = 'catalog.add_donor'
    model = Donor
    queryset = Donor.objects.all()

    def get_context_data(self, **kwargs):
        context = super(DonorListView, self).get_context_data(**kwargs)
        form_class = DonorEditForm
        context['create_item_form'] = form_class()
        context['nav_entities'] = True
        context['subnav_donors'] = True
        return context


class DonorUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    form_class = DonorEditForm
    permission_required = 'catalog.change_donor'
    model = Donor
    success_url = reverse_lazy('donor_list')
    template_name = 'catalog/donor_edit_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class DonorDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                      DeleteView):
    permission_required = 'catalog.delete_donor'
    model = Donor
    success_url = reverse_lazy('donor_list')
    cancel_url = success_url


#
# CRUD for DonorCode
#

class DonorCodeCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    permission_required = 'catalog.add_donorcode'
    model = DonorCode
    fields = ['code', 'donor_code_type']
    success_url = reverse_lazy('donorcode_list')
    template_name = 'catalog/donorcode_new_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "New donorcode added")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class DonorCodeListView(PermissionRequiredMixin, ListView):
    permission_required = 'catalog.add_donorcode'
    model = DonorCode
    fields = ['code', 'donor_code_type']
    queryset = DonorCode.objects.all()
    template_name = 'catalog/donorcode_list.html'

    def get_context_data(self, **kwargs):
        context = super(DonorCodeListView, self).get_context_data(**kwargs)
        form_class = model_forms.modelform_factory(self.model, fields=self.fields)
        context['create_item_form'] = form_class()
        context['nav_entities'] = True
        context['subnav_donorcodes'] = True
        return context


class DonorCodeUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    permission_required = 'catalog.change_donorcode'
    model = DonorCode
    fields = ['code', 'donor_code_type']
    success_url = reverse_lazy('donorcode_list')
    template_name = 'catalog/donorcode_edit_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class DonorCodeDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                          DeleteView):
    permission_required = 'catalog.delete_donorcode'
    model = DonorCode
    success_url = reverse_lazy('donorcode_list')
    cancel_url = success_url
