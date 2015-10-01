from django.conf.urls import include, url
from django.contrib.auth import views

from litrus.modules.accounts.views import *


urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', views.logout, { 'next_page': '/' }, name='logout'),
    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^email/validation/$', EmailValidationView.as_view(), name='email-validation'),
    url(r'^password/reset/$', PasswordResetView.as_view(), name='password-reset'),
    url(r'^subscription/$', SubscriptionView.as_view(), name='subscription'),
    url(r'^subscription/billing/$', SubscriptionBillingView.as_view(), name='subscription-billing'),
    url(r'^profile/$', ProfileView.as_view(), name='profile'),
    url(r'^profile/edit/$', ProfileEditView.as_view(), name='profile-edit'),
    url(r'^settings/$', SettingsView.as_view(), name='settings'),
]
