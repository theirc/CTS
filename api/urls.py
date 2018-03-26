from django.conf.urls import url, include

from rest_framework import routers

from api.viewsets import ItemCategoryViewSet, UserViewSet, \
    CatalogItemViewSet, ShipmentViewSet, TransporterViewSet, \
    PackageItemViewSet, PackageViewSet, KitViewSet, DonorViewSet, SupplierViewSet, \
    DonorCodeViewSet, PackageScanViewSet


router = routers.DefaultRouter()
# DRF insists on our adding base_name to these, even though we don't use it.
router.register(r'auth/users', UserViewSet, base_name='foo-auth-users')
router.register(r'catalog/items', CatalogItemViewSet, base_name='foo-catitems')
router.register(r'catalog/categories', ItemCategoryViewSet, base_name='foo-catcats')
router.register(r'catalog/kits', KitViewSet, base_name='foo-catkits')
router.register(r'entities/donors', DonorViewSet, base_name='foo-ent-donors')
router.register(r'entities/donorcodes', DonorCodeViewSet, base_name='foo-end-doncodes')
router.register(r'entities/suppliers', SupplierViewSet, base_name='foo-sup;iers')
router.register(r'entities/transporters', TransporterViewSet, base_name='foo-transpor')
router.register(r'shipments/packages', PackageViewSet, base_name='foo-pkgs')
router.register(r'shipments/packageitems', PackageItemViewSet, base_name='foo-items')
router.register(r'shipments/packagescans', PackageScanViewSet, base_name='foo-scans')
router.register(r'shipments/shipments', ShipmentViewSet, base_name='foo-ships')


urlpatterns = [
    url(r'^', include(router.urls)),
]
