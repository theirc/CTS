from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from .views import CatalogItemListView, CatalogItemDeleteView, \
    CatalogImportView, CatalogItemUpdateView, CatalogItemCreateView, \
    TransporterListView, TransporterDeleteView, TransporterUpdateView, \
    TransporterCreateView, SupplierListView, SupplierDeleteView, SupplierUpdateView, \
    SupplierCreateView, DonorListView, DonorDeleteView, DonorUpdateView, \
    DonorCreateView, KitCreateView, KitAddItemView, KitUpdateView, \
    KitDeleteView, KitItemDeleteView, CategoryListView, CategoryDeleteView, CategoryCreateView, \
    CategoryUpdateView, DonorCodeListView, DonorCodeDeleteView, DonorCodeCreateView, \
    DonorCodeUpdateView


urlpatterns = [
    url(r'^$', CatalogItemListView.as_view(), name='catalog_list'),
    url(r'^delete/(?P<pk>\d+)/$', CatalogItemDeleteView.as_view(), name='catalog_delete'),
    url(r'^import/$', CatalogImportView.as_view(), name='catalog_import_modal'),

    url(r'^new/$', CatalogItemCreateView.as_view(),
        name='new_catalog_item_modal'),
    url(r'^new/kit/$', KitCreateView.as_view(),
        name='new_kit_modal'),
    url(r'^add_to_kit/(?P<kit_pk>\d+)/(?P<item_pk>\d+)/(?P<quantity>\d+)/$',
        csrf_exempt(KitAddItemView.as_view()),
        name='add_item_to_kit'),
    url(r'^edit/(?P<pk>\d+)/$', CatalogItemUpdateView.as_view(),
        name='edit_catalog_item_modal'),

    url(r'^kit/delete/(?P<pk>\d+)/$', KitDeleteView.as_view(), name='kit_delete'),
    url(r'^kit/edit/(?P<pk>\d+)/$', KitUpdateView.as_view(), name='kit_edit_modal'),
    url(r'^kititem/delete/(?P<pk>\d+)/$', KitItemDeleteView.as_view(), name='kit_item_delete'),

    url(r'^transporters/$', TransporterListView.as_view(), name='transporter_list'),
    url(r'^transporters/delete/(?P<pk>\d+)/$',
        TransporterDeleteView.as_view(), name='transporter_delete'),
    url(r'^transporters/new/$', TransporterCreateView.as_view(),
        name='new_transporter_modal'),
    url(r'^transporters/edit/(?P<pk>\d+)/$', TransporterUpdateView.as_view(),
        name='edit_transporter_modal'),

    url(r'^suppliers/$', SupplierListView.as_view(), name='supplier_list'),
    url(r'^suppliers/delete/(?P<pk>\d+)/$', SupplierDeleteView.as_view(), name='supplier_delete'),
    url(r'^suppliers/new/$', SupplierCreateView.as_view(),
        name='new_supplier_modal'),
    url(r'^suppliers/edit/(?P<pk>\d+)/$', SupplierUpdateView.as_view(),
        name='edit_supplier_modal'),

    url(r'^donors/$', DonorListView.as_view(), name='donor_list'),
    url(r'^donors/delete/(?P<pk>\d+)/$', DonorDeleteView.as_view(), name='donor_delete'),
    url(r'^donors/new/$', DonorCreateView.as_view(),
        name='new_donor_modal'),
    url(r'^donors/edit/(?P<pk>\d+)/$', DonorUpdateView.as_view(),
        name='edit_donor_modal'),

    url(r'^categories/$', CategoryListView.as_view(), name='category_list'),
    url(r'^categories/delete/(?P<pk>\d+)/$', CategoryDeleteView.as_view(), name='category_delete'),
    url(r'^categories/new/$', CategoryCreateView.as_view(),
        name='new_category_modal'),
    url(r'^categories/edit/(?P<pk>\d+)/$', CategoryUpdateView.as_view(),
        name='edit_category_modal'),

    url(r'^donorcodes/$', DonorCodeListView.as_view(), name='donorcode_list'),
    url(r'^donorcodes/delete/(?P<pk>\d+)/$', DonorCodeDeleteView.as_view(),
        name='donorcode_delete'),
    url(r'^donorcodes/new/$', DonorCodeCreateView.as_view(),
        name='new_donorcode_modal'),
    url(r'^donorcodes/edit/(?P<pk>\d+)/$', DonorCodeUpdateView.as_view(),
        name='edit_donorcode_modal'),
]
