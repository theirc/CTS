from django.conf import settings


def currencies(request):
    return {
        'local_currency': settings.LOCAL_CURRENCY,
        'usd_currency': 'USD',
    }
