from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.ReportList.as_view(), name='reports_list'),
]

# Add a URL pattern for each report that extends from ReportBase.
for ReportClass in views.ReportBase.__subclasses__():
    urlpatterns += [ReportClass.get_url_pattern()]
