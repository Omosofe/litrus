from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from litrus.models import Course, DiscussionQuestion
from litrus.utils import is_user_enrolled


def course_required(view):
    """
    Grab course from url and check if exists.
    """
    def view_wrapper(request,  *args, **kwargs):
        kwargs['course'] = get_object_or_404(Course, slug=kwargs.get('slug'))
        # Enable staff users to see draft courses.
        if kwargs['course'].draft and not request.user.is_staff:
            raise Http404()
        return view(request,  *args, **kwargs)
    return view_wrapper


def user_enrolled_required(view):
    """
    Check if the user is enrolled to the course.
    It depends on `login_required` and `course_required`.
    """
    def view_wrapper(request,  *args, **kwargs):
        if is_user_enrolled(request.user, kwargs['course']) \
           or request.user.is_superuser:
        	return view(request,  *args, **kwargs)
        raise PermissionDenied
    return view_wrapper


def question_required(view):
    """
    Grab question from url and check if exists. Also check if the user
    logged owns the question.
    It depends on `login_required` and `course_required`.
    """
    def view_wrapper(request,  *args, **kwargs):
        kwargs['question'] = get_object_or_404(DiscussionQuestion,
                                             id=kwargs['question_id'],
                                             course=kwargs['course'])
        kwargs['user_owns_question'] = kwargs['question'].user == request.user

        return view(request,  *args, **kwargs)
    return view_wrapper
