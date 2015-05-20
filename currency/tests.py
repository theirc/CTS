import locale

from django.test import TestCase
from mock import patch
from currency.currencies import format_currency, currencies


class CurrencyTest(TestCase):
    def test_format_currency(self):
        # Test that our format_currency works the same as the built-in python locale.currency.

        # This doesn't provide complete coverage of the formatting code - we'd need to
        # use more currencies that have different formatting rules to do that - but this
        # should be good enough to make sure we're basically running it the same, and
        # we didn't really change that much of it anyway.
        val = 1.47
        for currency_code in currencies.keys():
            for symbol in [False, True]:
                for grouping in [False, True]:
                    for international in [False, True]:
                        our_output = format_currency(currency_code, val, symbol, grouping,
                                                     international)
                        with patch('locale.localeconv') as mock_localeconv:
                            mock_localeconv.return_value = currencies[currency_code]
                            built_in_output = locale.currency(val, symbol, grouping, international)
                        self.assertEqual(
                            built_in_output, our_output,
                            msg="Failure: Built-in returned %s, our code returned %s, for currency"
                                " %s symbol %s grouping %s international %s" %
                                (built_in_output, our_output, currency_code, symbol, grouping,
                                 international))
