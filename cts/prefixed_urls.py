from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView


# PREFIX_URL is either empty, or it starts with /
# and ends without a /. This is the one place that's not
# convenient and we need some conditional logic.
if settings.PREFIX_URL:
    PATTERN = r'^%s/' % settings.PREFIX_URL.lstrip('/')
else:
    PATTERN = r'^'


urlpatterns = patterns(
    '',
    url(PATTERN, include('cts.urls')),

    # If no prefix, redirect
    url(r'^$', RedirectView.as_view(permanent=False, pattern_name='instances')),
)
