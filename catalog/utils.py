import logging
import xlrd

from collections import OrderedDict

from django.db import transaction
from django.forms.utils import ErrorDict

from catalog.forms import CatalogItemImportForm


IMPORT_COLUMN_NAMES = [
    'item_code',
    'item_category',
    'description',
    'donor',
    'donor_t1',
    'supplier',
    'weight',
    'unit',
    'price_local',
    'price_usd',
]

# Give up import after this many errors
MAX_IMPORT_ERRORS = 50


logger = logging.getLogger(__name__)


class CatalogImportFailure(Exception):
    def __init__(self, errlist):
        self.errlist = errlist


class SimpleSheet(object):
    """
    Simplified interface to a sheet in an Excel spreadsheet.
    """
    def __init__(self, filename, sheet_number):
        try:
            book = xlrd.open_workbook(filename)
        except xlrd.XLRDError as e:
            raise CatalogImportFailure(errlist=e.args)
        if sheet_number >= book.nsheets:
            raise ValueError("No sheet number %d in this spreadsheet" % sheet_number)
        self.sheet = book.sheet_by_index(sheet_number)
        if not self.sheet.nrows:
            raise ValueError("Sheet %d has no rows" % sheet_number)

    def column_names(self):
        """
        Return values from first row
        """
        return self.sheet.row_values(0)

    def rows(self):
        """
        Generator that returns (row_number, ordered_dictionary_of_values) for each row.
        The row number is what a human would see, e.g. 1-based index.
        The first row - assumed to have column names - is omitted from this method's results.
        """
        names = self.column_names()
        for row_index in range(1, self.sheet.nrows):
            values = self.sheet.row_values(row_index)
            d = OrderedDict()
            for name, value in zip(names, values):
                d[name] = value
            yield (row_index + 1, d)


def format_form_errors(row_number, form):
    """
    Return form errors as a list of strings.
    """
    if isinstance(form.errors, ErrorDict):
        # keys are the field names
        errlist = []
        for field_name, list_of_errors in form.errors.items():
            for e in list_of_errors:
                if field_name == '__all__':
                    errlist.append('row %d: %s' % (row_number, e))
                else:
                    errlist.append('row %d: field %s: %s' % (row_number, field_name, e))
        return errlist


def catalog_import(path):
    """
    Import catalog items from a spreadsheet in the file at the given path.

    Assumes the first sheet has the data, the first row is the column names, and
    the columns we want to import have the same names as the fields in the model.

    If anything fails, raises CatalogImportFailure.

    If successful, returns the number of items imported
    """

    # It's not really necessary to break this code up into separate functions, but
    # it'll simplify testing.
    try:
        sheet = SimpleSheet(path, 0)
    except ValueError as e:
        raise CatalogImportFailure(errlist=e.args)
    return _catalog_import_from_simple_sheet(sheet)


def _catalog_import_from_simple_sheet(sheet):
    """import catalog items from a SimpleSheet instance"""

    # Make sure expected columns exist
    columns_not_found = (set(IMPORT_COLUMN_NAMES)
                         - set(sheet.column_names()))
    if columns_not_found:
        missing_cols = '%s ' * len(columns_not_found) % tuple(columns_not_found)
        raise CatalogImportFailure(errlist=["Some columns not found: %s" % missing_cols])

    # Start importing
    num_new = 0
    errors = []
    # import all, or none
    with transaction.atomic():
        for row_number, values in sheet.rows():
            try:
                num_new += 1
                form = CatalogItemImportForm(data=values)
                if form.is_valid():
                    form.save()
                else:
                    errors.extend(format_form_errors(row_number, form))
                    if len(errors) >= MAX_IMPORT_ERRORS:
                        errors.append("Giving up after %d errors" % MAX_IMPORT_ERRORS)
                        break
            except Exception as e:
                logger.exception("Importing %r" % values)
                errors.append("row %d: %s" % (row_number, e))
        if errors:
            raise CatalogImportFailure(errors)
    return num_new
