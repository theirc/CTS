from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from shipments import views


urlpatterns = [

    # Shipments
    url(r'^list/$',
        views.ShipmentsListView.as_view(), name='shipments_list'),
    url(r'^map/$',
        views.ShipmentsDashboardView.as_view(), name='shipments_dashboard'),
    url(r'^map/package/(?P<pk>\d+)/$',
        views.ShipmentsPackageMapView.as_view(), name='shipments_package_map'),
    url(r'^new/$',
        views.ShipmentCreateView.as_view(), name='create_shipment'),
    url(r'^shipment/(?P<pk>\d+)/$',
        views.ShipmentUpdateView.as_view(), name='edit_shipment'),
    url(r'^shipment/(?P<pk>\d+)/packages/$',
        gzip_page(csrf_exempt(views.ShipmentPackagesView.as_view())), name='shipment_packages'),
    url(r'^shipment/$',
        views.ShipmentUpdateView.as_view(), name='edit_shipment_no_pk'),
    url(r'^shipment/delete/(?P<pk>\d+)/$',
        views.ShipmentDeleteView.as_view(), name='delete_shipment'),
    url(r'^shipment/lost/(?P<pk>\d+)/$',
        views.ShipmentLostView.as_view(), name='lost_shipment'),
    url(r'^shipment/editlost/(?P<pk>\d+)/$',
        views.ShipmentEditLostView.as_view(), name='edit_lost_note'),

    # Packages
    url(r'^new/pkg/(?P<pk>\d+)/$',
        views.NewPackageModalView.as_view(), name='new_package'),
    url(r'^edit/pkg/(?P<pk>\d+)/$',
        views.EditPackageModalView.as_view(), name='edit_package'),
    url(r'^pkg_from_kit/(?P<pk>\d+)/$',
        views.NewPackageFromKitModalView.as_view(), name='new_package_from_kit'),
    url(r'^package/delete/(?P<pk>\d+)/$',
        views.PackageDeleteView.as_view(), name='package_delete'),

    # Package items
    url(r'^package/item/delete/(?P<pk>\d+)/$',
        views.PackageItemDeleteView.as_view(), name='package_item_delete'),
    url(r'^package/item/edit/(?P<pk>\d+)/$',
        views.PackageItemEditModalView.as_view(), name='package_item_edit'),
    url(r'^package/item/add/(?P<package_id>\d+)/$',
        views.PackageItemCreateModalView.as_view(), name='package_item_create'),
    url(r'^package/items/(?P<pk>\d+)/$',
        gzip_page(csrf_exempt(views.PackageItemsView.as_view())), name='package_items'),
    url(r'^package/items/bulk_edit/$',
        views.PackageItemsBulkEditView.as_view(), name='bulk_edit_package_items'),

    # Printing
    url(r'^manifest/summary/(?P<pk>\d+)/$',
        views.SummaryManifestView.as_view(), name='summary_manifests'),
    url(r'^manifest/detail/(?P<pk>\d+)/$',
        views.ShipmentDetailsView.as_view(), name='shipment_details'),
    url(r'^barcodes/(?P<pk>\d+)/(?P<size>\d+)/(?P<labels>.*)/$',
        views.PackageBarcodesView.as_view(), name='package_barcodes'),
    url(r'^manifest/full/(?P<pk>\d+)/(?P<size>\d+)/$',
        views.FullManifestsView.as_view(), name='full_manifests'),

    url(r'print/(?P<pk>\d+)/$',
        views.PrintView.as_view(), name='print'),

    url(r'^qrcode/(?P<code>.*)\.png$',
        views.qrcode_view,
        kwargs={'size': views.NORMAL_SIZE},
        name='qrcode'),
    url(r'^qrcode_l/(?P<code>.*)\.png$',
        views.qrcode_view,
        kwargs={'size': views.LARGE_SIZE},
        name='qrcode_l'),
    url(r'^qrcode_vl/(?P<code>.*)\.png$',
        views.qrcode_view,
        kwargs={'size': views.VERY_LARGE_SIZE},
        name='qrcode_vl'),
    url(r'^qrcode_s/(?P<size>\d+)/(?P<code>.*)\.png$',
        views.qrcode_view,
        kwargs={'size_in_centimeters': True},
        name='qrcode_sized'),
]
