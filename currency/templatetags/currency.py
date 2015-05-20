from django import template
from django.conf import settings

from .. import currencies


register = template.Library()


@register.simple_tag
def format_currency(currency_code, val,
                    symbol=True, grouping=True, international=False):
    if val in [None, ""]:
        return ''
    return currencies.format_currency(currency_code, val, symbol, grouping,
                                      international)


@register.filter
@register.simple_tag
def format_usd(val, symbol=True, grouping=True, international=False):
    currency_code = "USD"
    return format_currency(currency_code, val, symbol, grouping, international)


@register.filter
@register.simple_tag
def format_local(val, symbol=True, grouping=True, international=False):
    currency_code = settings.LOCAL_CURRENCY
    return format_currency(currency_code, val, symbol, grouping, international)
