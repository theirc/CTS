import rest_framework.urls
import selectable.urls
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
import django.contrib.auth.views
from django.views.generic import TemplateView

import accounts.urls
import api.urls
import catalog.urls
import reports.urls
import shipments.urls
from accounts.views import home_view
from cts.views import health_view


admin.autodiscover()


urlpatterns = [
    # Health check for load balancer
    url(r'^health/$', health_view, name='health'),

    url(r'^session_security/', include('session_security.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^catalog/', include(catalog.urls)),
    url(r'^reports/', include(reports.urls)),
    url(r'^shipments/', include(shipments.urls)),
    url(r'^users/', include(accounts.urls)),

    # Redirect '/' to some app the user has privs for
    url(r'^$', home_view, name='home'),
    # Special page to list available instances
    url(r'^instances/$', TemplateView.as_view(template_name='instances.html'), name='instances'),

    # REST
    # login-out for REST browsable API
    url(r'^api/auth/', include(rest_framework.urls, namespace='rest_framework')),
    # other REST API URLs
    url(r'^api/', include(api.urls)),
    url(r'^selectable/', include(selectable.urls)),
    # url(r'^apidocs/', include(rest_framework_swagger.urls)),  # FIXME: REPLACE THIS
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    url(r'^login/$', django.contrib.auth.views.login, {'template_name': 'login.html'},
        name='account_login'),
    url(r'^logout/$', django.contrib.auth.views.logout,
        {'next_page': '/'}, name='account_logout'),
    url(r'^password_change/$', django.contrib.auth.views.password_change,
        {'template_name': 'account/password_change_form.html'},
        name='password_change'),
    url(r'^password_change/done/$', django.contrib.auth.views.password_change_done,
        {'template_name': 'account/password_change_done.html'},
        name='password_change_done'),
    url(r'^password_reset/$', django.contrib.auth.views.password_reset,
        {'template_name': 'account/password_reset_form.html'},
        name='password_reset'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        django.contrib.auth.views.password_reset_confirm,
        {'template_name': 'account/password_reset_confirm.html'},
        name='password_reset_confirm'),
    url(r'^password_reset/done/$', django.contrib.auth.views.password_reset_done,
        {'template_name': 'account/password_reset_done.html'},
        name='password_reset_done'),
    url(r'^reset/done/$',
        django.contrib.auth.views.password_reset_complete,
        {'template_name': 'account/password_reset_complete.html'},
        name='password_reset_complete'),
]
