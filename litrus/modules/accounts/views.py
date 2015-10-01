from base64 import b16encode
from urllib import quote

from django.conf import settings
from django.contrib.auth import authenticate, login, REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, send_mail
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView, View
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from paypal.standard.forms import PayPalPaymentsForm

from litrus.models import *
from litrus.modules.accounts.decorators import *
from litrus.modules.accounts.forms import *
from litrus.utils import random_hash


class LoginView(View):
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        # Grab `next` value.
        kwargs[REDIRECT_FIELD_NAME] = request.POST.get(REDIRECT_FIELD_NAME,
            request.GET.get(REDIRECT_FIELD_NAME, ''))

        return super(self.__class__,
                     self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, kwargs)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username_or_email', '')
        try:
            user = User.objects.get(email=username)
            username = user.username
        except User.DoesNotExist:
            pass
        user = authenticate(username=username,
                            password=request.POST.get('password', ''))
        if user is not None:
            login(request, user)
            return redirect(kwargs[REDIRECT_FIELD_NAME] or 'accounts:profile')
        else:
            kwargs['error'] = _('Username and password did not match. Please try again.')

        return render(request, self.template_name, kwargs)


class RegisterView(FormView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'

    def form_valid(self, form):
        user = User(username=form.cleaned_data['username'].lower(),
                    email = form.cleaned_data['email'].lower())
        user.set_password(form.cleaned_data['password'])
        user.is_active = False
        user.save()

        # Generate the token.
        token, created = EmailValidationToken.objects.get_or_create(user=user)
        token.token = random_hash()
        token.save()

        # Create the email body.
        activation_link = settings.SITE_URL + token.get_absolute_url()
        html_content = render_to_string('accounts/emails/register.html',
            { 'activation_link': activation_link })

        # Send email to the user.
        msg = EmailMessage(_('Activate your account'), html_content, 'from@example.com', [user.email])
        msg.content_subtype = 'html'
        msg.send()

        redirect_url = reverse('accounts:email-validation') + '?email=' + quote(user.email)
        return redirect(redirect_url)


class EmailValidationView(View):
    template_send = 'accounts/email_validation_send.html'
    template_sent = 'accounts/email_validation_sent.html'

    def dispatch(self, request, *args, **kwargs):
        kwargs['token'] = request.GET.get('token')
        kwargs['email'] = request.GET.get('email')
        return super(self.__class__,
                     self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if kwargs['token']:
            # Grab token and validate account.
            try:
                token = PasswordResetToken.objects.get(token=kwargs['token'])
                token.user.is_active = True
                token.user.save()
            except PasswordResetToken.DoesNotExist:
                pass

            return redirect('accounts:login')
        if kwargs['email']:
            return render(request, self.template_sent, kwargs)

        return render(request, self.template_send, kwargs)


class PasswordResetView(View):
    template_email = 'accounts/password_reset_email.html'
    template_form = 'accounts/password_reset_form.html'
    template_sent = 'accounts/password_reset_sent.html'

    def dispatch(self, request, *args, **kwargs):
        kwargs['token'] = request.POST.get('token',
            request.GET.get('token', ''))
        kwargs['email'] = request.GET.get('email')
        return super(self.__class__,
                     self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if kwargs['token']:
            return render(request, self.template_form, kwargs)
        if kwargs['email']:
            return render(request, self.template_sent, kwargs)

        return render(request, self.template_email, kwargs)

    def post(self, request, *args, **kwargs):
        if kwargs['token']:
            try:
                token = PasswordResetToken.objects.get(token=kwargs['token'])
            except PasswordResetToken.DoesNotExist:
                kwargs['error'] = _('Your token for reseting password is invalid.')
                return render(request, self.template_form, kwargs)

            password = request.POST.get('password', '')
            password_again = request.POST.get('password_again', '')

            if len(password) < 6:
                kwargs['error'] = _('Your password is too short.')
                return render(request, self.template_form, kwargs)

            if not(password == password_again):
                kwargs['error'] = _('Your passwords mismatch.')
                return render(request, self.template_form, kwargs)

            token.user.set_password(password)
            token.user.save()
            token.delete()

            return redirect('accounts:login')
        else:
            email = request.POST.get('email', '')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                kwargs['error'] = _('The email is invalid.')
                return render(request, self.template_email, kwargs)

            # Generate the token.
            token, created = PasswordResetToken.objects.get_or_create(user=user)
            token.token = random_hash()
            token.save()

            reset_url = reverse('accounts:password-reset') + '?token=' + token.token

            send_mail(_('Password Reset'), reset_url, 'from@example.com',
                [email], fail_silently=False)

            redirect_url = reverse('accounts:password-reset') + '?email=' + quote(email)
            return redirect(redirect_url)


class SubscriptionView(TemplateView):
    template_name = 'accounts/subscription.html'

    @method_decorator(csrf_exempt)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        try:
            context['subscription'] = Subscription.objects.get(
                user=self.request.user)
        except Subscription.DoesNotExist:
            context['subscription'] = None

        return context


class SubscriptionBillingView(TemplateView):
    template_name = 'accounts/subscription_billing.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        context['plans'] = SubscriptionPlan.objects.order_by('level')

        for plan in context['plans']:
            paypal_dict = {
                'invoice': random_hash(),
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': plan.price,
                'item_number': plan.id,
                'item_name': plan.name,
                'custom': b16encode(self.request.user.email),
                'notify_url': settings.SITE_URL + reverse('paypal-ipn'),
                'return_url': settings.SITE_URL + reverse('accounts:subscription'),
                'cancel_return': settings.SITE_URL + reverse('accounts:subscription-billing'),
            }
            plan.form = PayPalPaymentsForm(initial=paypal_dict)

        return context


class ProfileView(TemplateView):
    template_name = 'accounts/profile.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        context['courses'] = Course.of_user(self.request.user)

        for course in context['courses']:
            course.date_enrolled = \
                CourseEnrollment.objects.get(
                    user=self.request.user, course=course).date_enrolled
            course.completed = \
                course.percentage_completed_of_user(self.request.user)[2]

        context['questions'] = DiscussionQuestion.objects.filter(
            user=self.request.user).order_by('-date_created')[:10]

        return context


class ProfileEditView(FormView):
    form_class = ProfileEditForm
    template_name = 'accounts/profile_edit.html'

    def get_initial(self):
        initial = super(self.__class__, self).get_initial()

        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name

        return initial

    def form_valid(self, form):
        user = self.request.user

        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']

        user.save()

        return redirect('accounts:profile-edit')

class SettingsView(TemplateView):
    template_name = 'accounts/settings.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)
