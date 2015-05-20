from django.core.management.base import BaseCommand
from accounts.utils import bootstrap_permissions


class Command(BaseCommand):
    args = '(no args)'
    help = 'Creates any missing Groups and Permissions'

    def handle(self, *args, **options):
        bootstrap_permissions()
        self.stdout.write("Sucessfully created any missing permissions and groups")
