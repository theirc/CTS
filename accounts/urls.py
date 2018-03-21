from django.conf.urls import url

from .views import CtsUserListView, CtsUserDeleteView, CtsUserUpdateView, CtsUserCreateView, \
    CtsUserResetAPITokenView, CtsUserBarcodeView, CtsUserSendPasswordReset


urlpatterns = [
    url(r'^$', CtsUserListView.as_view(), name='user_list'),
    url(r'^delete/(?P<pk>\d+)/$', CtsUserDeleteView.as_view(), name='user_delete'),
    url(r'^new/$', CtsUserCreateView.as_view(),
        name='new_cts_user_modal'),
    url(r'^edit/(?P<pk>\d+)/$', CtsUserUpdateView.as_view(),
        name='edit_cts_user_modal'),
    url(r'^reset_api_token/(?P<pk>[0-9a-z]+)/$', CtsUserResetAPITokenView.as_view(),
        name='reset_api_token'),
    url(r'^barcode/(?P<pk>\d+)/$', CtsUserBarcodeView.as_view(), name='user_barcode'),
    url(r'^sendreset/(?P<pk>\d+)/$', CtsUserSendPasswordReset.as_view(),
        name='send_password_reset_email'),
]
