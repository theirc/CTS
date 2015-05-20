from django.test import SimpleTestCase

from .. import utils
from cts.utils import is_int


class TestCamelToSpace(SimpleTestCase):
    tests = [
        ('lowercase', 'lowercase'),
        ('Title', 'Title'),
        ('CamelCase', 'Camel Case'),
        ('UPPERCASE', 'UPPERCASE'),
        ('PDFLoader', 'PDF Loader'),
        ('SimpleXMLParser', 'Simple XML Parser'),
        ('one_two_three', 'one_two_three'),
        ('aA_bB', 'a A_b B'),
        ('99Numbers', '99 Numbers'),
        ('99NUMBERS', '99 NUMBERS'),

        # NOTE: Method doesn't recognize numbers as a separate word.
        ('September4', 'September4'),
        ('ABC5000', 'ABC5000'),
        ('Aa99Bb', 'Aa99 Bb'),
    ]

    def test_camel_to_space(self):
        failures = []
        for test_string, expected in self.tests:
            actual = utils.camel_to_space(test_string)
            if actual != expected:
                failures.append((test_string, expected, actual))
        if failures:
            messages = ['"{}": expected "{}", got "{}"'.format(*f)
                        for f in failures]
            self.fail("{} test(s) failed:\n{}".format(
                len(failures), "\n".join(messages)))


class TestCamelToUnderscore(SimpleTestCase):
    tests = [
        ('lowercase', 'lowercase'),
        ('Title', 'Title'),
        ('CamelCase', 'Camel_Case'),
        ('UPPERCASE', 'UPPERCASE'),
        ('PDFLoader', 'PDF_Loader'),
        ('SimpleXMLParser', 'Simple_XML_Parser'),
        ('one_two_three', 'one_two_three'),
        ('aA_bB', 'a_A_b_B'),
        ('99Numbers', '99_Numbers'),
        ('99NUMBERS', '99_NUMBERS'),

        # NOTE: Method doesn't recognize numbers as a separate word.
        ('September4', 'September4'),
        ('ABC5000', 'ABC5000'),
        ('Aa99Bb', 'Aa99_Bb'),
    ]

    def test_camel_to_underscore(self):
        failures = []
        for test_string, expected in self.tests:
            actual = utils.camel_to_underscore(test_string)
            if actual != expected:
                failures.append((test_string, expected, actual))
        if failures:
            messages = ['"{}": expected "{}", got "{}"'.format(*f)
                        for f in failures]
            self.fail("{} test(s) failed:\n{}".format(
                len(failures), "\n".join(messages)))


class TestIsInt(SimpleTestCase):
    def test_is_int(self):
        for value, result in [
            ("1", True),
            ("", False),
            ("1,000", False),
            ("1.05", False),
            ("queryt", False),
            ("1234db", False),
            ("1_23", False),
        ]:
            self.assertEqual(result, is_int(value))
