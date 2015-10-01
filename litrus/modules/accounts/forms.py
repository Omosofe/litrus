from re import match

from django import forms
from django.contrib.auth.models import User
from django.core.validators import validate_email, EmailValidator
from django.utils.translation import ugettext_lazy as _


class RegisterForm(forms.Form):

    username = forms.CharField(label=_('Username'))
    email = forms.EmailField(label=_('Email'), validators=[EmailValidator])
    password = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput)
    password_again = forms.CharField(
        label=_('Password Again'), widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()

        cleaned_data['username'] = cleaned_data.get('username', '').lower()
        cleaned_data['email'] = cleaned_data.get('email', '').lower()
        cleaned_data['password'] = cleaned_data.get('password', '')
        cleaned_data['password_again'] = cleaned_data.get('password_again', '')


        # Username validation.
        if not (3 < len(cleaned_data['username']) < 20):
            raise forms.ValidationError(_('Username length may be between 3 and 20 characters.'))
        if not match(r'^[a-zA-Z]+$', cleaned_data['username']):
            raise forms.ValidationError(_('Username value may contain only letters and numbers.'))

        # Password validation.

        if not (cleaned_data['password'] == cleaned_data['password_again']):
            raise forms.ValidationError(_('Passwords must be equal.'))

        if not (len(cleaned_data['password']) >= 6):
            raise forms.ValidationError(_('Password must be 6 character length.'))

        # Ensure email is not already registered.
        try:
            User.objects.get(email=cleaned_data['email'])
            raise forms.ValidationError(_('The email is already registered.'))
        except User.DoesNotExist:
            pass

        # Ensure username is not already registered.
        try:
            User.objects.get(username=cleaned_data['username'])
            raise forms.ValidationError(_('The username is already registered.'))
        except User.DoesNotExist:
            pass


class ProfileEditForm(forms.Form):

    first_name = forms.CharField(
        label=_('First Name'), required=False)
    last_name = forms.CharField(
        label=_('Last Name'), required=False)

    def clean_first_name(self):
        data = self.cleaned_data['first_name']

        if data == '':
            return data
        if not match(r'^[a-zA-Z\s]{2,50}$', data):
            raise forms.ValidationError(_('First name may contain only letters.'))

        return data

    def clean_last_name(self):
        data = self.cleaned_data['last_name']

        if data == '':
            return data
        if not match(r'^[a-zA-Z\s]{2,50}$', data):
            raise forms.ValidationError(_('Last name may contain only letters.'))

        return data
