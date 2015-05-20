from django.conf import settings

import django_tables2 as tables

from currency.currencies import format_currency


class NumberColumn(tables.Column):
    """Base class for any numerical value."""

    def __init__(self, *args, **kwargs):
        """Align text in the column to the right."""
        attrs = kwargs.get('attrs', {})
        td_attrs = attrs.get('td', {})
        td_attrs['class'] = td_attrs.get('class', '') + 'text-right'
        attrs['td'] = td_attrs
        kwargs['attrs'] = attrs
        super(NumberColumn, self).__init__(*args, **kwargs)


class PercentageColumn(NumberColumn):

    def render(self, value):
        return '{}%'.format(value * 100)  # value is out of 1.


class LocalCurrencyColumn(NumberColumn):

    def render(self, value):
        currency_code = settings.LOCAL_CURRENCY
        return format_currency(currency_code, value)


class LocalCurrencyDownloadColumn(NumberColumn):
    """Preserves the value but returns it as a string"""

    def render(self, value):
        return str(value)


class USDCurrencyColumn(NumberColumn):

    def render(self, value):
        currency_code = "USD"
        return format_currency(currency_code, value)
