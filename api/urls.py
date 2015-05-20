from django.conf.urls import url, patterns, include

from rest_framework import routers

from api.viewsets import ItemCategoryViewSet, UserViewSet, \
    CatalogItemViewSet, ShipmentViewSet, TransporterViewSet, \
    PackageItemViewSet, PackageViewSet, KitViewSet, DonorViewSet, SupplierViewSet, DonorCodeViewSet, \
    PackageScanViewSet


router = routers.DefaultRouter()
router.register(r'auth/users', UserViewSet)
router.register(r'catalog/items', CatalogItemViewSet)
router.register(r'catalog/categories', ItemCategoryViewSet)
router.register(r'catalog/kits', KitViewSet)
router.register(r'entities/donors', DonorViewSet)
router.register(r'entities/donorcodes', DonorCodeViewSet)
router.register(r'entities/suppliers', SupplierViewSet)
router.register(r'entities/transporters', TransporterViewSet)
router.register(r'shipments/packages', PackageViewSet)
router.register(r'shipments/packageitems', PackageItemViewSet)
router.register(r'shipments/packagescans', PackageScanViewSet)
router.register(r'shipments/shipments', ShipmentViewSet)


urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
)
