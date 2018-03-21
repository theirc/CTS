from django.contrib.auth import get_user_model
import django_filters

from rest_framework import permissions, viewsets, serializers
from rest_framework.serializers import ModelSerializer

from catalog.models import CatalogItem, Transporter, ItemCategory, Donor, Supplier, \
    DonorCode
from shipments.models import Shipment, Package, PackageItem, Kit, PackageScan


class CTSPermissions(permissions.DjangoModelPermissions):
    # Require SOME permission on a model, even for a GET
    perms_map = {
        'GET': ['%(app_label)s.add_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


# Inherit from ReadOnlyModelViewSet because our API is read-only
class CTSViewSet(viewsets.ReadOnlyModelViewSet):
    # Django REST Framework will enforce Django model permissions on the API
    permission_classes = [CTSPermissions]


# Keep the following classes in alphabetical order, please.


class CatalogItemFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(name='item_category__name')
    description = django_filters.CharFilter(name='description')
    in_stock = django_filters.BooleanFilter(name='in_stock')
    unit = django_filters.CharFilter(name='unit')

    class Meta:
        model = CatalogItem
        fields = ['category', 'description', 'in_stock', 'unit']


class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem


class CatalogItemViewSet(CTSViewSet):
    filter_class = CatalogItemFilter
    model = CatalogItem
    ordering_fields = '__all__'
    queryset = model.objects.all()
    serializer_class = CatalogItemSerializer


class DonorViewSet(CTSViewSet):
    filter_fields = ['name']
    model = Donor


class DonorCodeViewSet(CTSViewSet):
    filter_fields = ['code', 'donor_code_type']
    model = DonorCode


class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory


class ItemCategoryViewSet(CTSViewSet):
    filter_fields = ['name']
    model = ItemCategory
    queryset = model.objects.all()
    serializer_class = ItemCategorySerializer


class KitViewSet(CTSViewSet):
    filter_fields = ['description', 'name']
    model = Kit


class PackageScanViewSet(CTSViewSet):
    model = PackageScan


class PackageItemFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(name='item_category__name')
    donor = django_filters.CharFilter(name='donor__name')
    supplier = django_filters.CharFilter(name='supplier__name')

    class Meta:
        fields = ['description', 'unit']
        model = PackageItem


class PackageItemViewSet(CTSViewSet):
    filter_class = PackageItemFilter
    model = PackageItem


class PackageSerializer(serializers.ModelSerializer):
    items = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                view_name='packageitem-detail')
    scans = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                view_name='packagescan-detail')

    class Meta:
        model = Package


class PackageViewSet(CTSViewSet):
    model = Package
    serializer_class = PackageSerializer


class ShipmentFilter(django_filters.FilterSet):
    min_shipment_date = django_filters.DateFilter(name="shipment_date", lookup_type='gte')
    max_shipment_date = django_filters.DateFilter(name="shipment_date", lookup_type='lte')
    partner = django_filters.CharFilter(name="partner__name")
    transporter = django_filters.CharFilter(name="transporter__name")

    class Meta:
        model = Shipment
        fields = ['status', 'description', 'shipment_date', 'store_release']


class ShipmentSerializer(serializers.ModelSerializer):
    packages = serializers.HyperlinkedRelatedField(many=True, read_only=True,
                                                   view_name='package-detail')

    class Meta:
        model = Shipment


class ShipmentViewSet(CTSViewSet):
    filter_class = ShipmentFilter
    model = Shipment
    serializer_class = ShipmentSerializer


class SupplierViewSet(CTSViewSet):
    filter_fields = ['name']
    model = Supplier


class TransporterViewSet(CTSViewSet):
    filter_fields = ['name']
    model = Transporter


class UserSerializer(ModelSerializer):
    class Meta:
        fields = ['email', 'is_active', 'is_staff', 'is_superuser', 'name',
                  'mobile', 'code', 'skype', 'notes', 'role']
        model = get_user_model()


class UserViewSet(CTSViewSet):
    filter_fields = ['email', 'is_active', 'is_staff', 'is_superuser',
                     'name', 'mobile', 'code', 'skype', 'notes', 'role']
    model = get_user_model()
    queryset = model.objects.all()
    serializer_class = UserSerializer
