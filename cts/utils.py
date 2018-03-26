from decimal import Decimal
import json
from math import floor
import re
from time import time

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db.models import DecimalField


class DecimalEncoder(json.JSONEncoder):
    # JSON serialization for Decimal values
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


encoder = DecimalEncoder()


def json_encode(data):
    return encoder.encode(data)


class FormErrorReturns400Mixin(object):
    def form_invalid(self, form):
        # If the form is not valid, return the usual page but with a 400 status
        return self.render_to_response(self.get_context_data(form=form), status=400)


class DeleteViewMixin(object):
    """
    Use common delete confirm template, and
    provide the "cancel_url" attribute of the view in the context.
    (Override `get_cancel_url` if the URL needs to be dynamically computed.)
    """
    template_name = "cts/confirm_delete.html"

    def get_cancel_url(self):
        return self.cancel_url

    def get_context_data(self, **kwargs):
        context = super(DeleteViewMixin, self).get_context_data(**kwargs)
        context['cancel_url'] = self.get_cancel_url()
        return context


def uniqid():
    """
    Like PHP's `uniqid`.

    Gets a unique identifier based on the current time in microseconds.

    :return: string with the unique identifier
    """

    # per http://us1.php.net/manual/en/function.uniqid.php#95001
    # For the record, the underlying function to uniqid() appears to be roughly as follows:

    # $m=microtime(true);
    # sprintf("%8x%05x\n",floor($m),($m-floor($m))*1000000);
    #
    # In other words, first 8 hex chars = Unixtime, last 5 hex chars = microseconds.
    # This is why it has microsecond precision.

    t = time()
    return "%8x%05x" % (floor(t), (t - floor(t)) * 1000000)


def camel_to_space(name):
    """Convert a string in "CamelCase" to "Camel Case"."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)


def camel_to_underscore(name):
    """Convert a string in "CamelCase" to "camel_case"."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)


def context_processor(request):
    """Make `settings` available in templates.
    Also whether to limit data to what a partner can see.
    """
    # Note: this gets run even on pages like login and 404, so
    # must work if user is not authenticated.
    from accounts.models import more_than_partner  # Avoid circular import

    return {
        'settings': settings,
        # 'more_than_partner' is True if user has more privileges than a Partner
        'more_than_partner': more_than_partner(request.user),
    }


def make_form_readonly(form):
    """
    Set some attributes on a form's fields that, IN COMBINATION WITH TEMPLATE CHANGES,
    allow us to display it as read-only.
    """

    # Note that a new BoundField is constructed on the fly when you access
    # form[name], so any data we want to persist long enough for the template
    # to access needs to be on the "real" field.  We just use the BoundField
    # to get at the field value.

    for name in form.fields:
        field = form.fields[name]
        bound_field = form[name]
        if hasattr(field.widget, 'choices'):
            try:
                display_value = dict(field.widget.choices)[bound_field.value()]
            except KeyError:
                display_value = ''
        else:
            display_value = bound_field.value()

        field.readonly = True
        field.display_value = display_value


def is_int(value):
    try:
        int(value)
    except ValueError:
        return False
    else:
        return True


class USDCurrencyField(DecimalField):
    """
    DecimalField with useful defaults for USD currency.

    IRC has requested that we track USD amounts to 3 decimal places.
    """
    def __init__(self, max_digits=10, decimal_places=3, default=Decimal('0.00'), **kwargs):
        validators = kwargs.pop('validators', [MinValueValidator(0.0)])
        super(USDCurrencyField, self).__init__(
            max_digits=max_digits,
            decimal_places=decimal_places,
            validators=validators,
            default=default,
            **kwargs
        )


def not_falsey(iterable):
    return [
        x
        for x in iterable
        if x
    ]