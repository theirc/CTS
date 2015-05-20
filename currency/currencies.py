"""
Currencies we might need to use.

The key is the international symbol, e.g. "USD" for US Dollars.

The value is the dictionary returned by locale.localeconv() when the
locale is set to a locale that uses the currency. (Not all items in
the dictionary are relevant to currency, and the non-relevant ones don't
need to be here, but they don't hurt anything.)

If you need to add a currency, see the function below the dictionary
in this file.
"""
import locale
from decimal import Decimal

from django.conf import settings


currencies = {
    # US Dollar
    'USD': {'mon_decimal_point': '.', 'int_frac_digits': 2, 'p_sep_by_space': 0, 'frac_digits': 2,
            'thousands_sep': ',', 'n_sign_posn': 1, 'decimal_point': '.', 'int_curr_symbol': 'USD ',
            'n_cs_precedes': 1, 'p_sign_posn': 1, 'mon_thousands_sep': ',', 'negative_sign': '-',
            'currency_symbol': '$', 'n_sep_by_space': 0, 'mon_grouping': [3, 3, 0],
            'p_cs_precedes': 1, 'positive_sign': '', 'grouping': [3, 3, 0]},
    # Jordanian dinar
    'JOD': {'mon_decimal_point': '.', 'int_frac_digits': 3, 'p_sep_by_space': 1, 'frac_digits': 3,
            'thousands_sep': ',', 'n_sign_posn': 2, 'decimal_point': '.', 'int_curr_symbol': 'JOD ',
            'n_cs_precedes': 1, 'p_sign_posn': 1, 'mon_thousands_sep': ',', 'negative_sign': '-',
            'currency_symbol': '\xd8\xaf.\xd8\xa3.', 'n_sep_by_space': 1, 'mon_grouping': [3, 0],
            'p_cs_precedes': 1, 'positive_sign': '', 'grouping': [3, 0]},
    # Turkish lira
    'TRY': {'mon_decimal_point': ',', 'int_frac_digits': 2, 'p_sep_by_space': 1, 'frac_digits': 2,
            'thousands_sep': '.', 'n_sign_posn': 1, 'decimal_point': ',', 'int_curr_symbol': 'TRY ',
            'n_cs_precedes': 0, 'p_sign_posn': 1, 'mon_thousands_sep': '.', 'negative_sign': '-',
            'currency_symbol': 'YTL', 'n_sep_by_space': 1, 'mon_grouping': [3, 3, 0],
            'p_cs_precedes': 0, 'positive_sign': '', 'grouping': [3, 3, 0]},
    # Iraqi dinar
    'IQD': {'mon_decimal_point': '.', 'int_frac_digits': 3, 'p_sep_by_space': 1, 'frac_digits': 3,
            'thousands_sep': ',', 'n_sign_posn': 2, 'decimal_point': '.', 'int_curr_symbol': 'IQD ',
            'n_cs_precedes': 1, 'p_sign_posn': 1, 'mon_thousands_sep': ',', 'negative_sign': '-',
            'currency_symbol': '\xd8\xaf.\xd8\xb9.', 'n_sep_by_space': 1, 'mon_grouping': [3, 0],
            'p_cs_precedes': 1, 'positive_sign': '', 'grouping': [3, 0]},
    # Made-up currency to improve test coverage
    'TST': {'mon_decimal_point': '.', 'int_frac_digits': 3, 'p_sep_by_space': 1, 'frac_digits': 3,
            'thousands_sep': ',', 'n_sign_posn': 2, 'decimal_point': '.', 'int_curr_symbol': 'IQD ',
            'n_cs_precedes': 1, 'p_sign_posn': 1, 'mon_thousands_sep': ',', 'negative_sign': '-',
            'currency_symbol': '\xd8\xaf.\xd8\xb9.', 'n_sep_by_space': 1, 'mon_grouping': None,
            'p_cs_precedes': 1, 'positive_sign': '+', 'grouping': [3, 0]},
}


CURRENCY_CHOICES = [
    ('USD', 'USD'),
    (settings.LOCAL_CURRENCY, settings.LOCAL_CURRENCY),
]


def lookup_currency(locale_name):  # pragma: no cover
    """
    This is a helper to get information about a new currency.

    Start a python shell, import this function, and call it with a
    locale name that uses the currency.  It'll print
    out the dictionary to copy/paste into the above data structure.

    To find valid locale names on your system, run "locale -a".

    If you don't see the locale you need, and you're on a Debian-based
    system, you can install a language-pack package that includes data
    for the language or country you need.  E.g. "language-pack-ar" and
    "language-pack-ar-base" provide the data for all Arabic-speaking
    countries, or "language-pack-tr" and "language-pack-base-tr" for
    Turkish.

    So to lookup the data for US Dollars, you'd pass "en_US.utf8"; for
    Jordanian dinars, "ar_JO.utf8"
    """
    import locale
    locale.setlocale(locale.LC_ALL, locale_name)
    conv = locale.localeconv()
    print(repr(conv))


def quantize_usd(dec):
    """Given a Decimal, limit to 2 decimal places (USD uses 2 decimals)"""
    fp = Decimal(10) ** -2
    return dec.quantize(fp)


def quantize_local(dec):
    """
    Given a decimal, limit to the number of decimal places for the
    local currency.
    """
    decimal_places = currencies[settings.LOCAL_CURRENCY]['int_frac_digits']
    fp = Decimal(10) ** -decimal_places
    return dec.quantize(fp)


################################################################################
#
# Misc. code copied from Python 2.7 `locale` and modified so we can format
# different currencies, instead of always assuming the global locale.
#
################################################################################

def _group(conv, s, monetary=False):
    thousands_sep = conv[monetary and 'mon_thousands_sep' or 'thousands_sep']
    grouping = conv[monetary and 'mon_grouping' or 'grouping']
    if not grouping:
        return (s, 0)
    if s[-1] == ' ':
        stripped = s.rstrip()
        right_spaces = s[len(stripped):]
        s = stripped
    else:
        right_spaces = ''
    left_spaces = ''
    groups = []
    for interval in locale._grouping_intervals(grouping):
        if not s or s[-1] not in "0123456789":
            # only non-digit characters remain (sign, spaces)
            left_spaces = s
            s = ''
            break
        groups.append(s[-interval:])
        s = s[:-interval]
    if s:
        groups.append(s)
    groups.reverse()
    return (
        left_spaces + thousands_sep.join(groups) + right_spaces,
        len(thousands_sep) * (len(groups) - 1)
    )


def format(conv, percent, value, grouping=False, monetary=False):
    """Returns the locale-aware substitution of a %? specifier
    (percent).
    """
    # this is only for one-percent-specifier strings and this should be checked
    match = locale._percent_re.match(percent)
    if not match or len(match.group()) != len(percent):  # pragma: no cover
        raise ValueError(("format() must be given exactly one %%char "
                         "format specifier, %s not valid") % repr(percent))
    return _format(conv, percent, value, grouping, monetary)


def _format(conv, percent, value, grouping=False, monetary=False):
    formatted = percent % value
    # floats and decimal ints need special action!
    if percent[-1] in 'eEfFgG':
        seps = 0
        parts = formatted.split('.')
        if grouping:
            parts[0], seps = _group(conv, parts[0], monetary=monetary)
        decimal_point = conv[monetary and 'mon_decimal_point'
                             or 'decimal_point']
        formatted = decimal_point.join(parts)
        if seps:
            formatted = locale._strip_padding(formatted, seps)
    elif percent[-1] in 'diu':
        seps = 0
        if grouping:
            formatted, seps = _group(conv, formatted, monetary=monetary)
        if seps:
            formatted = locale._strip_padding(formatted, seps)
    return formatted


def format_currency(currency_code, val, symbol=True, grouping=False, international=False):
    """
    :param currency_code: International code for the currency, e.g. 'USD' or 'JOD.
    :param val: The value
    :returns: A string with the value formatted as the given currency.
    """
    conv = currencies[currency_code]

    # check for illegal values
    digits = conv[international and 'int_frac_digits' or 'frac_digits']
    if digits == 127:  # pragma: no cover
        raise ValueError("Currency formatting is not possible using "
                         "the 'C' locale.")

    # noinspection PyStringFormat
    s = format(conv, '%%.%if' % digits, abs(val), grouping, monetary=True)
    # '<' and '>' are markers if the sign must be inserted between symbol and value
    s = '<' + s + '>'

    if symbol:
        smb = conv[international and 'int_curr_symbol' or 'currency_symbol']
        precedes = conv[val < 0 and 'n_cs_precedes' or 'p_cs_precedes']
        separated = conv[val < 0 and 'n_sep_by_space' or 'p_sep_by_space']

        if precedes:
            s = smb + (separated and ' ' or '') + s
        else:
            s = s + (separated and ' ' or '') + smb

    sign_pos = conv[val < 0 and 'n_sign_posn' or 'p_sign_posn']
    sign = conv[val < 0 and 'negative_sign' or 'positive_sign']

    if sign_pos == 0:
        s = '(' + s + ')'
    elif sign_pos == 1:
        s = sign + s
    elif sign_pos == 2:
        s = s + sign
    elif sign_pos == 3:
        s = s.replace('<', sign)
    elif sign_pos == 4:
        s = s.replace('>', sign)
    else:
        # the default if nothing specified;
        # this should be the most fitting sign position
        s = sign + s

    return s.replace('<', '').replace('>', '')
