from __future__ import unicode_literals

from django.contrib.auth.models import Group, AbstractBaseUser, \
    PermissionsMixin, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cts.utils import uniqid

# Role implementation notes:

# There's a Django group with the same name as each role (e.g. 'coordinator').
# Ownership of a role is implemented by membership in the corresponding group.

# If new roles are added, use a new migration to make sure the corresponding
# groups are created and given the appropriate permissions.

# Similarly, if there's a change to the permissions given to a role, use a new migration
# to make the change in the database. The permissions
# corresponding to a role are only represented in the migrations.

# 'coordinator' implies 'officer'
# Rather than continually having to check whether a user has any of multiple roles,
# we ensure when a user's roles are edited that if they are given a role,
# they are put in all the groups implied by that role.


ROLE_COORDINATOR = 'coordinator'
# The IRC Coordinator is the administrator of the Supply Chain System. He/She is the only
# user permitted to enter and view Referrer, Transporter and Receiver/End User data.
# The Monitoring Manager reports to the Coordinator.

ROLE_MANAGER = 'manager'
# The Monitoring Manager is a primary user of the system. The system is designed to
# enable the Monitoring Manager to aid with the project's required monitoring and
# reporting. The Monitoring Manager reports to the Coordinator.
# (the monitoring manager's privileges are currently the same as the monitoring officer)

ROLE_OFFICER = 'officer'
# Monitoring Officer - IRC Warehouse staff, who will create and update a catalog of items,
# receive shipments ("stock in"), and create packages that can be combined into shipments.
# Reports to the Monitoring Manager.

ROLE_PARTNER = 'partner'
# Recipient  - These may be doctors, clinics, or service provision organizations
# operating inside Syria and responding to the medical needs of conflict-affected
# Syrians. IRC will aim to have approximate 20 approved end-users by the end of the
# project. Recipients, also known as "End Users" or "Network",

ROLE_REFERRER = 'referrer'
# Referrer - leftover from CTS v2, no real meaning in v3.  Only exists
# if such users were migrated from v2.

ROLE_RECIPIENT = 'recipient'
# Recipient - another holdover from v2

ROLE_CHOICES = [
    (ROLE_COORDINATOR, 'Coordinator'),
    (ROLE_MANAGER, 'Monitoring manager'),
    (ROLE_OFFICER, 'Monitoring officer'),
    (ROLE_PARTNER, 'Partner'),
]

IMPLIED_ROLES = {
    ROLE_COORDINATOR: [ROLE_MANAGER, ROLE_OFFICER],
    ROLE_MANAGER: [ROLE_OFFICER],
}

# These only need to include the additional permissions over and above any
# permissions that are provided by implied roles.
perms = ['view', 'add', 'change', 'delete']
ROLE_PERMISSIONS = {
    ROLE_PARTNER: [
        'shipments.view_%s' % model
        for model in ['shipment', 'package', 'packageitem', 'kit', 'kititem', 'packagescan']
    ],
    ROLE_OFFICER:
        ['reports.view_all_partners'] +
        ['catalog.%s_%s' % (perm, model) for perm in perms
         for model in ['catalogitem', 'itemcategory']] +
        ['shipments.%s_%s' % (perm, model) for perm in perms
         for model in ['shipment', 'package', 'packageitem', 'kit', 'kititem', 'packagescan']],
    ROLE_MANAGER: [],
    ROLE_COORDINATOR:
        ['accounts.%s_%s' % (perm, model) for perm in perms for model in ['ctsuser']] +
        ['catalog.%s_%s' % (perm, model) for perm in perms
         for model in ['partner', 'supplier', 'transporter', 'donor', 'donorcode']]
}
del perms


class CtsUserManager(BaseUserManager):

    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class CtsUser(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(_('name'), max_length=60, blank=True, default='')
    email = models.EmailField(_('email address'), blank=False, unique=True, max_length=250)
    is_staff = models.BooleanField(
        _('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(
        _('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    mobile = models.CharField(
        max_length=45, blank=True, default='',
        validators=[
            RegexValidator(
                r'^\+?[0-9\-\(\) \.]*$',
                '+999-999-999 format, + and - are optional',
                'Invalid Phone Number'
            ), ]
    )
    code = models.CharField(max_length=45, blank=True, default='')
    deviceid = models.CharField(max_length=128, blank=True, default='')
    skype = models.CharField(
        max_length=50, blank=True, default='',
        validators=[
            RegexValidator(
                r'^[a-z][a-z0-9\.,\-_]{5,31}$',
                'Skype name must be between 6-32 characters, start with a '
                'letter and contain only letters and numbers (no spaces or '
                ' special characters)',
                'Invalid Skype Username'
            ), ]
    )
    notes = models.TextField(blank=True, default='')
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_PARTNER,
        help_text="User's main role (might imply some permissions of other roles)",
    )
    referrer_id = models.IntegerField(blank=True, null=True)
    city_id = models.IntegerField(blank=True, null=True)

    # For partners:
    colour = models.CharField(
        max_length=7, blank=True, default='',
        validators=[
            RegexValidator(
                r'^#(?:[0-9a-fA-F]{3}){1,2}$',
                '#AAA or #ABCDEF hex code',
                'Invalid Hex Color'
            ), ]
    )

    objects = CtsUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return self.name or self.email

    def save(self, *args, **kwargs):
        # make sure the User has a code (for QR)
        if not self.code:
            self.code = uniqid()
            while CtsUser.objects.filter(code=self.code).exists():
                self.code = uniqid()
        # Make sure user is in the right groups for their role
        super(CtsUser, self).save(*args, **kwargs)
        if self.pk:
            current_roles = set([group.name for group in self.groups.all()])
            if self.is_superuser:
                # All roles
                role_names = ROLE_PERMISSIONS.keys()
                self.add_roles(set(role_names) - current_roles)
            else:
                desired_roles = set([self.role]) | set(IMPLIED_ROLES.get(self.role, []))
                self.add_roles(desired_roles - current_roles)
                self.remove_roles(current_roles - desired_roles)

    def has_role(self, role_name):
        return self.groups.filter(name=role_name).exists()

    def add_role(self, role_name):
        self.groups.add(Group.objects.get(name=role_name))

    def add_roles(self, role_names):
        if role_names:
            groups = Group.objects.filter(name__in=role_names)
            self.groups.add(*groups)

    def remove_roles(self, role_names):
        if role_names:
            groups = Group.objects.filter(name__in=role_names)
            self.groups.remove(*groups)

    def get_roles(self):
        """Return list of role names this user has"""
        role_names = ROLE_PERMISSIONS.keys()
        return list(self.groups.filter(name__in=role_names).values_list('name', flat=True))

    def reset_api_token(self):
        from rest_framework.authtoken.models import Token
        if hasattr(self, 'auth_token'):
            self.auth_token.delete()
        Token.objects.create(user=self)

    def get_short_name(self):
        return self.name

    def is_just_partner(self):
        """User has partner role and no other roles and is not a superuser"""
        return not self.is_superuser and (self.get_roles() == [ROLE_PARTNER])


def more_than_partner(user):
    """
    Return True if user is authenticated and has more privs than a mere partner.
    """
    return user.is_authenticated() and (user.is_superuser or (ROLE_PARTNER not in user.get_roles()))


# When a user is created, give them an API token
@receiver(post_save, sender=CtsUser)
def create_api_token(sender, instance=None, created=False, **kwargs):
    from rest_framework.authtoken.models import Token
    if created:
        Token.objects.create(user=instance)
