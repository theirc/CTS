from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import ugettext_lazy as _

from accounts.models import CtsUser
from accounts.utils import canonical_email


CTS_USER_FIELDS = [
    'name',
    'email',
    'mobile',
    'skype',
    'role',
    'is_active',
    'colour',
    'password1',
    'password2'
]


class CtsUserEditForm(forms.ModelForm):
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    password1 = forms.CharField(label=_("Password"), required=False)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        help_text=_("Enter the same password as above, for verification."),
        required=False)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('initial', {})
        kwargs['initial']['password1'] = ''
        kwargs['initial']['password2'] = ''
        super(CtsUserEditForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = canonical_email(self.cleaned_data['email'])
        qset = CtsUser.objects.filter(email__iexact=email)
        if self.instance.pk:
            qset = qset.exclude(pk=self.instance.pk)
        if qset.exists():
            raise forms.ValidationError(
                self.error_messages['duplicate_email'],
                code='duplicate_email')
        return email

    def clean(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        if bool(password1) != bool(password2):
            raise forms.ValidationError("Enter password twice (or leave both fields blank)")
        return self.cleaned_data

    def save(self, *args, **kwargs):
        self.cleaned_data.pop('password1')
        password = self.cleaned_data.pop('password2')
        if self.instance.pk:
            # Just updating an existing user
            self.instance.save()
            user = self.instance
        else:
            user = CtsUser.objects.create_user(
                password=CtsUser.objects.make_random_password(),
                **self.cleaned_data
            )
        if password:
            user.set_password(password)
            user.save()
        return user

    class Meta:
        model = CtsUser
        fields = CTS_USER_FIELDS


class CtsUserChangeForm(forms.ModelForm):
    # This one is used only in the Django admin, not in our user-visible pages
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = CtsUser
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CtsUserChangeForm, self).__init__(*args, **kwargs)
        f = self.fields.get('user_permissions', None)
        if f is not None:
            f.queryset = f.queryset.select_related('content_type')

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class CtsUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """
    # This one is used only in the Django admin, not in our user-visible pages
    error_messages = {
        'duplicate_email': _("A user with that email already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    email = forms.EmailField()
    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = CtsUser
        fields = ("email",)

    def clean_email(self):
        # Since CtsUser.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        email = self.cleaned_data["email"]
        try:
            CtsUser._default_manager.get(email=email)
        except CtsUser.DoesNotExist:
            return email
        raise forms.ValidationError(self.error_messages['duplicate_email'])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(CtsUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
