from braces.views import LoginRequiredMixin, PermissionRequiredMixin, AjaxResponseMixin, \
    JSONResponseMixin, MultiplePermissionsRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, \
    FormView, View
from django.views.generic.detail import SingleObjectMixin
from accounts.models import CtsUser, ROLE_PARTNER
from catalog.models import Donor
from catalog.views import FormErrorReturns400Mixin
from cts.utils import DeleteViewMixin, make_form_readonly
from qrcode import QRCode, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_L
from shipments.forms import SHIPMENT_FIELDS, ShipmentEditForm, \
    NewPackageFromKitForm, PackageCreateForm, \
    PackageEditForm, PackageItemEditForm, PackageItemCreateForm, \
    ShipmentLostForm, PackageItemBulkEditForm, PrintForm, PRINT_FORMAT_SUMMARY, PRINT_FORMAT_FULL, \
    PRINT_FORMAT_DETAILS, PRINT_FORMAT_CODES, QRCODE_FORMATS, LABEL_FORMATS
from shipments.models import Shipment, ShipmentDBView, PackageDBView, Package, PackageItem, Kit
from shipments.tasks import delete_shipment


class ShipmentPartnerMixin(object):
    """
    Generic view mixin to restrict view of shipments for partner users
    to those associated with that partner.
    Also, returns Shipments on a POST, but ShipmentDBViews on a GET.
    Unless permit_view is False, then it always uses Shipments.
    """
    def get_shipment_queryset(self, permit_view=True):
        """Method to explicitly get shipment objects"""
        model = Shipment if self.request.method == 'POST' or not permit_view else ShipmentDBView
        queryset = model.objects.all()
        if self.request.user.is_just_partner():
            queryset = queryset.filter(partner=self.request.user)
        return queryset

    def get_queryset(self):
        """Classes with this mixin will by default get shipments if they call self.get_queryset()
        due to this method, but they can override it if they want and just invoke
        get_shipment_queryset when they need it. """
        return self.get_shipment_queryset()


class ShipmentsListView(PermissionRequiredMixin, ShipmentPartnerMixin, ListView):
    permission_required = 'shipments.view_shipment'
    model = ShipmentDBView
    template_name = 'shipments/list.html'

    def get_queryset(self):
        # Override so we can prefetch_related
        return self.get_shipment_queryset().prefetch_related('partner')

    def get_context_data(self, **kwargs):
        context = super(ShipmentsListView, self).get_context_data(**kwargs)
        context['nav_shipments'] = True
        return context


class ShipmentCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    fields = SHIPMENT_FIELDS
    form_class = ShipmentEditForm
    permission_required = 'shipments.add_shipment'
    model = Shipment
    template_name = 'shipments/create_edit_shipment.html'

    def creating(self):
        return True

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "New shipment added")
        return redirect('edit_shipment', pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(ShipmentCreateView, self).get_context_data(**kwargs)
        context['shipment'] = context['object'] = self.object
        return context


class ShipmentPackagesView(PermissionRequiredMixin, TemplateView):
    """
    Return the HTML for the rows of the shipment packages table.
    """
    permission_required = 'shipments.view_package'
    template_name = 'shipments/shipment_packages.html'

    def dispatch(self, request, *args, **kwargs):
        query_kwargs = {'pk': kwargs['pk']}
        if self.request.user.is_just_partner():
            query_kwargs['partner'] = self.request.user
        self.shipment = get_object_or_404(Shipment, **query_kwargs)
        return super(ShipmentPackagesView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ShipmentPackagesView, self).get_context_data(**kwargs)
        context['shipment'] = self.shipment
        # Look up packages in the view so we get the stats for free
        context['packages'] = PackageDBView.objects.filter(
            shipment=self.shipment).order_by('number_in_shipment')
        return context


class ShipmentUpdateView(MultiplePermissionsRequiredMixin, FormErrorReturns400Mixin,
                         ShipmentPartnerMixin, UpdateView):
    form_class = ShipmentEditForm
    permissions = {
        'any': ['shipments.change_shipment', 'shipments.view_shipment']
    }
    model = Shipment
    template_name = 'shipments/create_edit_shipment.html'

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        form = super(ShipmentUpdateView, self).get_form(form_class)
        if not self.request.user.has_perm('shipments.change_shipment'):
            make_form_readonly(form)
        return form

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(ShipmentUpdateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm('shipments.change_shipment'):
            return self.no_permissions_fail(request)
        self.object = self.get_object()
        if 'finalize' in request.POST:
            if not self.object.may_finalize():
                messages.error(request, "Cannot finalize a shipment in this state")
            else:
                self.object.finalize()
                messages.info(request, "Shipment finalized")
        elif 'cancel_shipment' in request.POST:
            if not self.object.may_cancel():
                messages.error(request, "Cannot cancel a shipment in this state")
            else:
                self.object.cancel()
                messages.info(request, "Shipment canceled")
        elif 'reopen_shipment' in request.POST:
            if not self.object.may_reopen():
                messages.error(request, "Cannot re-open a shipment in this state")
            else:
                self.object.reopen()
                messages.info(request, "Shipment reopened")
        else:
            return super(ShipmentUpdateView, self).post(request, *args, **kwargs)
        return redirect('edit_shipment', pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(ShipmentUpdateView, self).get_context_data(**kwargs)
        # Look up packages in the view so we get the stats for free
        context['packages'] = PackageDBView.objects.filter(
            shipment=self.object).order_by('number_in_shipment')
        context['shipment'] = self.object
        # We're just populating the shipments dropdown and don't need to compute
        # the shipment prices etc, so skip the expensive query on the SQL View
        # and just use the regular table
        context['shipments'] = self.get_shipment_queryset(permit_view=False)\
            .select_related('partner')
        return context

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        return redirect('edit_shipment', pk=self.object.pk)


class ShipmentLostView(PermissionRequiredMixin, FormErrorReturns400Mixin,
                       ShipmentPartnerMixin, SingleObjectMixin, FormView):
    form_class = ShipmentLostForm
    permission_required = 'shipments.change_shipment'
    template_name = 'shipments/lost_shipment.html'

    def dispatch(self, request, *args, **kwargs):
        self.shipment = self.object = self.get_object()
        return super(ShipmentLostView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        return {
            'acceptable': self.shipment.acceptable,
            'notes': self.shipment.status_note,
        }

    def form_valid(self, form):
        was_lost = self.shipment.is_lost()
        self.shipment.status = Shipment.STATUS_LOST
        self.shipment.acceptable = form.cleaned_data['acceptable']
        self.shipment.status_note = form.cleaned_data['notes']
        self.shipment.save()
        if not was_lost:
            messages.info(self.request, "Shipment marked as lost")
        return redirect('edit_shipment', pk=self.shipment.pk)


class ShipmentEditLostView(ShipmentLostView):
    permission_required = 'shipments.change_shipment'


class ShipmentDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                         DeleteView):
    permission_required = 'shipments.delete_shipment'
    model = Shipment
    success_url = reverse_lazy('shipments_list')
    cancel_url = success_url

    def delete(self, request, *args, **kwargs):
        shipment = self.get_object()
        delete_shipment.delay(shipment.pk)
        messages.info(request, "Shipment will be deleted in the background.  "
                               "It should be gone within a few minutes.")
        return HttpResponseRedirect(self.success_url)


# Ajax
class NewPackageFromKitModalView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    form_class = NewPackageFromKitForm
    permission_required = 'shipments.add_package'
    model = Package
    template_name = 'shipments/new_package_from_kit_modal.html'

    def dispatch(self, request, *args, **kwargs):
        self.shipment = get_object_or_404(Shipment, pk=kwargs['pk'])
        return super(NewPackageFromKitModalView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(NewPackageFromKitModalView, self).get_form_kwargs()
        kwargs['shipment'] = self.shipment
        initial = kwargs.get('initial', {})
        initial['package_quantity'] = 1
        kwargs['initial'] = initial
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(NewPackageFromKitModalView, self).get_context_data(**kwargs)
        context['kits'] = Kit.objects.all()
        return context

    def form_valid(self, form):
        packages = form.save()
        num_packages = packages.count()
        messages.info(self.request, "Created %d package%s" %
                      (num_packages, '' if num_packages == 1 else 's'))
        # Return the PK of the created package for the page to use
        return HttpResponse(str(packages[0].pk))

    def form_invalid(self, form):
        # Include the previously chosen quantities in the re-displayed modal's fields.
        # We'll stash them as attributes on the kits where the template can get them.
        context = self.get_context_data(form=form)
        for kit in context['kits']:
            k = 'kit-quantity-%d' % kit.pk
            if k in self.request.POST and self.request.POST[k]:
                kit.quantity = int(self.request.POST[k])
        return self.render_to_response(context, status=400)


class NewPackageModalView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    form_class = PackageCreateForm
    permission_required = 'shipments.add_package'
    model = Package
    template_name = 'shipments/new_package_modal.html'

    def dispatch(self, request, *args, **kwargs):
        self.shipment = get_object_or_404(Shipment, pk=kwargs['pk'])
        return super(NewPackageModalView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(NewPackageModalView, self).get_form_kwargs()
        kwargs['shipment'] = self.shipment
        initial = kwargs.get('initial', {})
        initial['package_quantity'] = 1
        kwargs['initial'] = initial
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(NewPackageModalView, self).get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        packages = form.save()
        num_packages = packages.count()
        messages.info(self.request, "Created %d package%s" %
                      (num_packages, '' if num_packages == 1 else 's'))
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class EditPackageModalView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    form_class = PackageEditForm
    permission_required = 'shipments.change_package'
    model = Package
    template_name = 'shipments/edit_package_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        return HttpResponse()


class PackageItemsView(PermissionRequiredMixin, TemplateView):
    """
    Return the HTML for the rows of the package items table.
    """
    permission_required = 'shipments.view_package'
    template_name = 'shipments/package_items.html'

    def dispatch(self, request, *args, **kwargs):
        query_kwargs = {'pk': kwargs['pk']}
        if self.request.user.is_just_partner():
            query_kwargs['shipment__partner'] = self.request.user
        self.package = get_object_or_404(Package, **query_kwargs)
        return super(PackageItemsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PackageItemsView, self).get_context_data(**kwargs)
        context['package'] = self.package
        context['package_items'] = self.package.items.all()
        return context


class PackageDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                        DeleteView):
    permission_required = 'shipments.delete_package'
    model = Package

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL.
        """
        self.object = self.get_object()
        self.object.items.all().delete()
        return super(PackageDeleteView, self).delete(request, *args, **kwargs)

    def get_success_url(self):
        shipment = self.object.shipment
        return reverse('edit_shipment', kwargs={'pk': shipment.pk})

    get_cancel_url = get_success_url


class PackageItemCreateModalView(PermissionRequiredMixin, FormErrorReturns400Mixin, FormView):
    form_class = PackageItemCreateForm
    permission_required = 'shipments.add_packageitem'
    template_name = 'shipments/create_package_item_modal.html'

    def dispatch(self, request, *args, **kwargs):
        package_id = kwargs['package_id']
        self.package = get_object_or_404(Package, pk=package_id)
        return super(PackageItemCreateModalView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Item added.")
        return HttpResponse()

    def get_form_kwargs(self):
        kwargs = super(PackageItemCreateModalView, self).get_form_kwargs()
        kwargs['package'] = self.package
        return kwargs


class PackageItemEditModalView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    form_class = PackageItemEditForm
    permission_required = 'shipments.change_packageitem'
    model = PackageItem
    template_name = 'shipments/edit_package_item_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        return HttpResponse()


class PackageItemDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                            DeleteView):
    permission_required = 'shipments.delete_packageitem'
    model = PackageItem

    def get_success_url(self):
        shipment = self.object.package.shipment
        return reverse('edit_shipment', kwargs={'pk': shipment.pk})

    get_cancel_url = get_success_url


class PackageItemsBulkEditView(PermissionRequiredMixin, FormErrorReturns400Mixin, FormView):
    form_class = PackageItemBulkEditForm
    permission_required = 'shipments.change_packageitem'
    model = PackageItem
    template_name = 'shipments/bulk_edit_package_items_modal.html'

    def get_selected_item_pks(self):
        if self.request.method == 'GET':
            pks = self.request.GET.get('selected_items', '').split(',')
        elif self.request.method == 'POST':
            # On POST, the list is in an input field
            pks = self.request.POST['selected_items'].split(',')
        return [int(pk) for pk in pks if pk]

    def form_valid(self, form):
        kwargs = {k: v for k, v in form.cleaned_data.items() if v}
        count = PackageItem.objects.filter(pk__in=self.get_selected_item_pks()).update(**kwargs)
        messages.info(self.request, "Changes saved to %d items" % count)
        return HttpResponse()


#
# PRINTING
#


class SummaryManifestView(MultiplePermissionsRequiredMixin,
                          ShipmentPartnerMixin,
                          SingleObjectMixin,
                          ListView):
    permissions = {
        'all': ['shipments.view_package', 'shipments.view_shipment']
    }
    template_name = 'shipments/summary_manifest.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object(queryset=self.get_shipment_queryset())
        return super(SummaryManifestView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return Package.objects.filter(shipment=self.object)

    def get_context_data(self, **kwargs):
        context = super(SummaryManifestView, self).get_context_data(**kwargs)
        context['shipment'] = self.object
        context['packages'] = Package.objects.filter(shipment=self.object)
        if 'size' in self.kwargs:
            # qrcode size in cm
            context['size'] = self.kwargs['size']
        return context


class ShipmentDetailsView(SummaryManifestView):
    template_name = 'shipments/shipment_details.html'


NORMAL_SIZE = ''
LARGE_SIZE = 'l'
VERY_LARGE_SIZE = 'vl'

LEVEL = {
    NORMAL_SIZE: ERROR_CORRECT_M,
    LARGE_SIZE: ERROR_CORRECT_Q,
    VERY_LARGE_SIZE: ERROR_CORRECT_L,
}

SIZE = {
    NORMAL_SIZE: 4,   # 84x84 pixels?
    LARGE_SIZE: 10,    # 210x210 pixels?
    VERY_LARGE_SIZE: 100,  # 2100x2100 pixels? ridiculous but seems to be what CTS v2 uses
}


def qrcode_view(request, code, size, size_in_centimeters=False):

    if size_in_centimeters:
        size = int(size)
        if size <= 6:
            size = NORMAL_SIZE
        elif size <= 8:
            size = LARGE_SIZE
        else:
            size = VERY_LARGE_SIZE
        qr = QRCode(
            error_correction=LEVEL[size],
            box_size=SIZE[size],
            border=0,
        )
    else:
        qr = QRCode(
            error_correction=LEVEL[size],
            box_size=SIZE[size],
            border=0,
        )
    qr.add_data(code)
    img = qr.make_image()

    rsp = HttpResponse(content_type='image/png')
    img.save(rsp)

    return rsp


class PrintView(MultiplePermissionsRequiredMixin,
                ShipmentPartnerMixin,
                FormView):
    form_class = PrintForm
    permissions = {
        'all': ['shipments.view_package', 'shipments.view_shipment']
    }
    template_name = 'shipments/print.html'

    def form_valid(self, form):
        format = form.cleaned_data['print_format']
        success_url_name = {
            PRINT_FORMAT_SUMMARY: 'summary_manifests',
            PRINT_FORMAT_FULL: 'full_manifests',
            PRINT_FORMAT_DETAILS: 'shipment_details',
            PRINT_FORMAT_CODES: 'package_barcodes',
        }[format]
        kwargs = {'pk': self.kwargs['pk']}
        if format in QRCODE_FORMATS:
            kwargs['size'] = form.cleaned_data['qrcode_size']
        if format in LABEL_FORMATS:
            kwargs['labels'] = ','.join(form.cleaned_data['labels'])
        success_url = reverse(success_url_name, kwargs=kwargs)
        return redirect(success_url)


class PackageBarcodesView(SummaryManifestView):
    template_name = 'shipments/package_barcodes.html'

    def get_context_data(self, **kwargs):
        context = super(PackageBarcodesView, self).get_context_data(**kwargs)
        context['labels'] = [int(x) for x in self.kwargs['labels'].split(',')]
        return context

    def get(self, request, *args, **kwargs):
        rsp = super(PackageBarcodesView, self).get(request, *args, **kwargs)
        # Mark shipment and packages ready for pickup if they haven't been already
        Shipment.objects.filter(pk=self.object.pk, status=Shipment.STATUS_IN_PROGRESS)\
            .update(status=Shipment.STATUS_READY)
        Package.objects.filter(shipment_id=self.object.pk, status=Shipment.STATUS_IN_PROGRESS)\
            .update(status=Shipment.STATUS_READY)
        return rsp


class FullManifestsView(SummaryManifestView):
    template_name = 'shipments/full_manifest.html'

    def get(self, request, *args, **kwargs):
        rsp = super(FullManifestsView, self).get(request, *args, **kwargs)
        # Mark shipment and packages ready for pickup if they haven't been already
        Shipment.objects.filter(pk=self.object.pk, status=Shipment.STATUS_IN_PROGRESS)\
            .update(status=Shipment.STATUS_READY)
        Package.objects.filter(shipment_id=self.object.pk, status=Shipment.STATUS_IN_PROGRESS)\
            .update(status=Shipment.STATUS_READY)
        return rsp


class ShipmentsDashboardView(LoginRequiredMixin, JSONResponseMixin, AjaxResponseMixin,
                             ShipmentPartnerMixin, View):
    """
    Shipment Dashboard View
    """
    template_name = 'shipments/dashboard.html'

    def _shipments_aggregates(self, shipments):
        packages = shipments.aggregate(pkg_count=Sum('num_packages'))
        items = PackageDBView.objects.filter(
            shipment_id__in=shipments.values('id')
        ).aggregate(item_count=Sum('num_items'))
        partners = CtsUser.objects.filter(
            id__in=shipments.values('partner__id')
        )
        value = shipments.aggregate(
            sum_price_usd=Sum('price_usd'),
            sum_price_local=Sum('price_local')
        )
        return packages, items, partners, value

    def get(self, request, *args, **kwargs):
        if request.user.is_just_partner():
            partners = [request.user]
        else:
            partners = CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
        donors = Donor.objects.all()
        shipments = self.get_shipment_queryset().order_by('description')

        context = {}
        context['shipments'] = shipments
        context['partners'] = partners
        context['donors'] = donors

        return render(request, self.template_name, context)

    def get_ajax(self, request, *args, **kwargs):
        shipments = self.get_shipment_queryset().order_by('description')
        if request.user.is_just_partner():
            partners = [request.user]
        else:
            partners = CtsUser.objects.filter(role=ROLE_PARTNER).order_by('name')
        data = {
            'partner_options': [(x.id, x.name) for x in partners],
            'shipment_options': [(x.id, x.__unicode__()) for x in shipments],
        }
        if request.GET:
            reset = request.GET.get('reset', '')
            if reset:
                data['shipments'] = {}
            else:
                shipment_filter = request.GET.get('shipment-pk', '')
                partner_filter = request.GET.get('partner-pk', '')
                donor_filter = request.GET.get('donor-pk', '')
                if shipment_filter:
                    shipments = shipments.filter(id=shipment_filter)
                if partner_filter:
                    shipments = shipments.filter(partner__id=partner_filter)
                if donor_filter:
                    donor = Donor.objects.get(pk=donor_filter)
                    pkg_ids = donor.packageitem_set.values_list('package_id', flat=True)
                    shipments = shipments.filter(packages__in=pkg_ids)
                shipments = ShipmentDBView.objects.filter(
                    id__in=shipments.values_list('id', flat=True)
                ).order_by('description')

                map_data = []
                for shipment in shipments:
                    shipment_data = {
                        'descr': shipment.__unicode__(),
                        'colour': shipment.partner.colour,
                        'locations': shipment.locations
                    }
                    map_data.append(shipment_data)

                # Delivered Shipments
                d_shipments = shipments.filter(status=Shipment.STATUS_RECEIVED)
                d_packages, d_items, d_partners, d_value = self._shipments_aggregates(d_shipments)
                # Undelivered Shipments
                u_shipments = shipments.exclude(status=Shipment.STATUS_RECEIVED)
                u_packages, u_items, u_partners, u_value = self._shipments_aggregates(u_shipments)

                if donor_filter:
                    # get options for dropdowns
                    partners = CtsUser.objects.filter(
                        id__in=shipments.values('partner__id')
                    )
                    data['partner_options'] = [(x.id, x.name) for x in partners]
                    data['shipment_options'] = [(x.id, x.__unicode__()) for x in shipments]

                data['shipments'] = map_data
                data['delivered'] = {
                    'packages': d_packages,
                    'items': d_items,
                    'partners': ', '.join([x.name for x in d_partners]) or None,
                    'total_value': d_value,
                    'number': d_shipments.count()
                }
                data['undelivered'] = {
                    'packages': u_packages,
                    'items': u_items,
                    'partners': ', '.join([x.name for x in u_partners]) or None,
                    'total_value': u_value,
                    'number': u_shipments.count()
                }
            return self.render_json_response(data)


class ShipmentsPackageMapView(MultiplePermissionsRequiredMixin, JSONResponseMixin,
                              AjaxResponseMixin, View):
    """
    Shipment Package Map View
    """
    permissions = {
        'all': ['shipments.view_package', 'shipments.view_shipment']
    }
    template_name = 'shipments/map_package.html'

    def get_package(self, request, pk):
        query_kwargs = {'pk': pk}
        if request.user.is_just_partner():
            query_kwargs['shipment__partner'] = request.user
        return get_object_or_404(Package, **query_kwargs)

    def get(self, request, pk, **kwargs):
        package = self.get_package(request, pk)

        context = {
            'package': package,
            'local_currency_symbol': settings.LOCAL_CURRENCY
        }
        return render(request, self.template_name, context)

    def get_ajax(self, request, pk, **kwargs):
        package = self.get_package(request, pk)
        package_data = {
            'descr': package.shipment.__unicode__(),
            'colour': package.shipment.partner.colour,
            'locations': package.scans_data
        }
        return self.render_json_response(package_data)
