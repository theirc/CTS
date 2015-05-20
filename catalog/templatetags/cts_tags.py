from django import template
from django.forms.forms import BoundField
from django.utils.encoding import force_text


register = template.Library()


@register.filter()
def getfield(form, name):
    """
    Return the named boundfield from the form.

    Usage: {{ form|getfield:name }}
    """
    try:
        field = form.fields[name]
    except KeyError:
        raise KeyError('Key %r not found in Form' % name)
    return BoundField(form, field, name)


@register.filter()
def concat(a, b):
    """
    Coerce both args to strings and concatenate them.
    (Contrast to "add", which tries to coerce its args to
    integers first.)
    """
    return force_text(a) + force_text(b)
