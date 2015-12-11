"""
Manually run the task that queries Ona for new form submissions
and processes them.
"""

import logging

from django.core.management.base import NoArgsCommand

from ona.tasks import process_new_scans


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Be verbose about what's going on in ona module
        # by adding a logger to stdout with level debug.
        logger = logging.getLogger('ona')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

        process_new_scans()
