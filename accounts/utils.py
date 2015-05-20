# -*- coding: utf-8 -*-
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Permission, Group
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.contenttypes.models import ContentType

from accounts.models import IMPLIED_ROLES, ROLE_PERMISSIONS


def get_permission_by_name(perm):
    app_label, codename = perm.split('.', 1)
    action, model = codename.split('_', 1)
    content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
    permission, _ = Permission.objects.get_or_create(codename=codename,
                                                     content_type=content_type,
                                                     defaults={
                                                         'name': 'Can %s %s' % (action, model),
                                                     })
    return permission


def get_role_permissions(role_name):
    """
    Return all the permission objects that the named role should have,
    taking into account implied permissions.
    """
    result = set([get_permission_by_name(perm)
                  for perm in ROLE_PERMISSIONS[role_name]])
    for implied_role in IMPLIED_ROLES.get(role_name, []):
        result |= get_role_permissions(implied_role)
    return result


def bootstrap_permissions():
    # This needs to be idempotent and efficient. It can get called repeatedly.

    # What are all the permissions that we currently grant this way?
    role_permissions = set([get_permission_by_name(perm)
                            for role_name, perms in ROLE_PERMISSIONS.items()
                            for perm in perms])

    for role_name in ROLE_PERMISSIONS:
        # Ensure group exists
        group, created = Group.objects.get_or_create(name=role_name)
        # Make sure group has the expected permissions
        expected_permissions = get_role_permissions(role_name)
        if created:
            group.permissions.add(*list(expected_permissions))
        else:
            # Which permissions, out of those we control this way, does the
            # group currently have?
            current_permissions = set(group.permissions.all()) & role_permissions
            perms_to_add = expected_permissions - current_permissions
            if perms_to_add:
                group.permissions.add(*list(perms_to_add))
            perms_to_remove = current_permissions - expected_permissions
            if perms_to_remove:
                group.permissions.remove(*list(perms_to_remove))


def send_user_password_reset_email(user, request, new_user):
    """
    Send a password reset email to the user.  The http request object is
    also required in order to figure out the URL to include in the email.

    :param user: CtsUser
    :param request: HttpRequest
    :param new_user: Whether user is new
    """
    # Code copied and adapted from django.contrib.auth.views.password_reset().
    form_data = {
        'email': user.email,
    }
    reset_form = PasswordResetForm(form_data)
    if reset_form.is_valid():
        opts = {
            'use_https': request.is_secure(),
            'token_generator': PasswordResetTokenGenerator(),
            'from_email': None,
            'request': request,
        }
        if new_user:
            opts['email_template_name'] = 'accounts/new_account_email.html'
            opts['subject_template_name'] = 'accounts/new_account_subject.txt'
        else:
            opts['email_template_name'] = 'accounts/password_reset_email.html'
            opts['subject_template_name'] = 'accounts/password_reset_subject.txt'
        reset_form.save(**opts)


def canonical_email(email):
    """
    Return canonical version of the email address.

    That is, force the part after @ to lowercase.
    """
    name, domain = email.split('@')
    return '%s@%s' % (name, domain.lower())
