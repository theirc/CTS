from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, UpdateView, DeleteView, CreateView, View, DetailView

from braces.views import PermissionRequiredMixin

from accounts.forms import CtsUserEditForm
from accounts.models import CtsUser
from accounts.utils import send_user_password_reset_email
from cts.utils import FormErrorReturns400Mixin, DeleteViewMixin


#
# CRUD for Users
#

class CtsUserSendPasswordReset(PermissionRequiredMixin, View):
    permission_required = 'accounts.add_ctsuser'

    def get(self, request, *args, **kwargs):
        user_pk = kwargs['pk']
        user = get_object_or_404(CtsUser, pk=user_pk)
        send_user_password_reset_email(user, request, new_user=False)
        messages.info(request, "Password reset email has been sent to %s." % user.email)
        return redirect('user_list')


class CtsUserCreateView(PermissionRequiredMixin, FormErrorReturns400Mixin, CreateView):
    permission_required = 'accounts.add_ctsuser'
    form_class = CtsUserEditForm
    initial = {'is_active': True, 'name': '', 'email': ''}
    model = CtsUser
    success_url = reverse_lazy('user_list')
    template_name = 'accounts/ctsuser_new_modal.html'

    def form_valid(self, form):
        # Was password provided?
        password_provided = bool(form.cleaned_data['password2'])

        self.object = form.save()

        if password_provided:
            messages.info(self.request, "New user added.")
        else:
            # Email new user a link to set their password.
            send_user_password_reset_email(user=self.object, request=self.request, new_user=True)
            messages.info(self.request,
                          "New user added. Email sent to %s with link for user to "
                          "choose initial password." % self.object.email)

        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class CtsUserListView(PermissionRequiredMixin, ListView):
    form_class = CtsUserEditForm
    permission_required = 'accounts.add_ctsuser'  # There is no read or view permission
    model = CtsUser
    queryset = CtsUser.objects.all()

    def get_context_data(self, **kwargs):
        context = super(CtsUserListView, self).get_context_data(**kwargs)
        context['create_item_form'] = self.form_class()
        context['nav_users'] = True
        return context


class CtsUserUpdateView(PermissionRequiredMixin, FormErrorReturns400Mixin, UpdateView):
    form_class = CtsUserEditForm
    permission_required = 'accounts.change_ctsuser'
    model = CtsUser
    success_url = reverse_lazy('user_list')
    template_name = 'accounts/ctsuser_edit_modal.html'

    def form_valid(self, form):
        self.object = form.save()
        messages.info(self.request, "Changes saved")
        # This is just a modal, no point in rendering a response
        return HttpResponse('')


class CtsUserDeleteView(PermissionRequiredMixin, FormErrorReturns400Mixin, DeleteViewMixin,
                        DeleteView):
    permission_required = 'accounts.delete_ctsuser'
    model = CtsUser
    success_url = reverse_lazy('user_list')
    cancel_url = success_url

    def delete(self, request, *args, **kwargs):
        """
        Don't really delete, just change to not active.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.is_active = False
        self.object.save()
        messages.info(request, "User has been changed to inactive. "
                               "You can re-activate the user by editing them and checking "
                               "the 'active' checkbox. "
                               "(Users are never really deleted since there might be shipments "
                               "still associated with them.)")
        return HttpResponseRedirect(success_url)


# View that just redirects to some view the user has privs for
def home_view(request):
    if not request.user.is_authenticated():
        return redirect(settings.LOGIN_URL)
    if request.user.has_module_perms('catalog'):
        return redirect('catalog_list')
    return redirect('reports_list')


# Change user's API token
class CtsUserResetAPITokenView(PermissionRequiredMixin, View):
    http_method_names = ['post']
    permission_required = 'accounts.change_ctsuser'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(CtsUser, pk=kwargs['pk'])
        user.reset_api_token()
        messages.info(self.request, "A new API token has been set for %s." % user)
        return redirect('user_list')


class CtsUserBarcodeView(DetailView):
    model = CtsUser
    template_name = 'accounts/ctsuser_barcode.html'
