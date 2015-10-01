from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import redirect

from litrus.models import *
from litrus.utils import *


def login_required(view):
    """
    Ensure the user is logged in.
    """
    def view_wrapper(request,  *args, **kwargs):
        if request.user.is_authenticated():
            return view(request,  *args, **kwargs)
        else:
            if request.is_ajax():
                return JsonResponse({ 'error': 'You must login first.' })
            else:
                path = request.get_full_path()
                return redirect_to_login(path)
    return view_wrapper


def subscription_required(view):
    """
    Check if the user is subscribed. This assumes that the
    user is logged in, so use `login_required` before.
    """
    def view_wrapper(request,  *args, **kwargs):
        if is_user_subscribed(request.user):
            return view(request,  *args, **kwargs)
        else:
            if request.is_ajax():
                return JsonResponse({ 'error': 'You must be subscribed.' })
            else:
                return redirect('accounts:subscription')
    return view_wrapper
