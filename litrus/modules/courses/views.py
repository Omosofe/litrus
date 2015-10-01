from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView, View
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from litrus.models import *
from litrus.modules.accounts.decorators import *
from litrus.modules.courses.decorators import course_required, user_enrolled_required, question_required
from litrus.utils import is_user_subscribed


class CoursesView(TemplateView):
    template_name = 'courses/courses.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        name_search = self.request.GET.get('search', '')
        category_search = self.request.GET.get('category', '')
        
        courses_query = Course.objects.filter(draft=False)
        if name_search:
            context['courses'] = courses_query.filter(
                                     name__contains=name_search)
        elif category_search:
            context['courses'] = courses_query.filter(
                                     category__slug=category_search)
        else:
            context['courses'] = courses_query.all()

        context['categories'] = CourseCategory.objects.all()

        return context


class CourseView(TemplateView):
    template_name = 'courses/course.html'

    def dispatch(self, request, *args, **kwargs):
        kwargs['course'] = get_object_or_404(Course, slug=kwargs['slug'],
                                             draft=False)

        return super(self.__class__, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            context['user_enrolled'] = CourseEnrollment.objects.filter(
                                           user=self.request.user,
                                           course=kwargs['course']).count()

        return context


class CourseEnrollmentView(View):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        course_id = request.POST.get('course_id')
        try:
            kwargs['course'] = Course.objects.get(id=course_id, draft=False)
            if not kwargs['course'].public and \
               not is_user_subscribed(request.user):
                return redirect('accounts:subscription')
            else:
                return super(self.__class__,
                             self).dispatch(request, *args, **kwargs)
        except Course.DoesNotExist:
            return redirect('courses:courses')

    def post(self, request, *args, **kwargs):
        # Create course enrollment.
        try:
            CourseEnrollment(user=request.user, course=kwargs['course']).save()
        except IntegrityError:
            # User is already enrolled. But no problem.
            pass

        return redirect(kwargs['course'].get_dashboard_url())


class CourseDashboardView(TemplateView):
    template_name = 'courses/course_dashboard.html'

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        context['course'] = kwargs['course']

        lessons, context['lessons_taken'], context['completed'] = \
            kwargs['course'].percentage_completed_of_user(self.request.user)

        # Generate url for next lesson.
        if not context['lessons_taken']:
            try:
                context['next_lesson_url'] = \
                    kwargs['course'].get_lesson_url(lessons[0])
            except IndexError:
                context['next_lesson_url'] = None
        else:
            last_lesson_taken = context['lessons_taken'][-1]
            try:
                next_lesson_id = lessons[lessons.index(last_lesson_taken) + 1]
                context['next_lesson_url'] = \
                    kwargs['course'].get_lesson_url(next_lesson_id)
            except IndexError:
                context['next_lesson_url'] = None

        return context


class CourseLessonView(TemplateView):
    template_name = 'courses/course_lesson.html'

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    def dispatch(self, request, *args, **kwargs):
        kwargs['lesson'] = get_object_or_404(CourseLesson,
                                        id=kwargs.get('lesson_id'),
                                        section__course=kwargs['course'],
                                        draft=False)

        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)


class UserFinishLessonView(View):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        lesson_id = request.POST.get('lesson_id', '')
        try:
            self.lesson = CourseLesson.objects.get(id=lesson_id, draft=False)

            return super(self.__class__, self).dispatch(
                request, *args, **kwargs)
        except CourseLesson.DoesNotExist:
            return redirect('accounts:profile')

    def post(self, request, *args, **kwargs):
        try:
            UserLesson(user=request.user, lesson=self.lesson).save()
        except IntegrityError:
            # User has taken the lesson before. But no problem.
            pass

        return redirect('courses:course-dashboard', slug=self.lesson.section.course.slug)


class CourseDiscussionView(TemplateView):
    template_name = 'courses/course_discussion.html'

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    def dispatch(self, request, *args, **kwargs):
        kwargs['page'] = request.GET.get('page')

        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)

        questions = DiscussionQuestion.objects.filter(
            course=kwargs['course']).order_by('-date_created')

        paginator = Paginator(questions, 8)

        try:
            context['questions'] = paginator.page(kwargs['page'])
        except PageNotAnInteger:
            context['questions'] = paginator.page(1)
        except EmptyPage:
            context['questions'] = paginator.page(paginator.num_pages)

        context['questions_count'] = paginator.count
        context['questions_closed_count'] = \
            questions.filter(is_open=False).count()

        context['recent_comments'] = DiscussionComment.objects.filter(
            question__course=kwargs['course'])\
            .order_by('-date_created')[:6]

        context['users_enrolled_count'] = \
            CourseEnrollment.objects.filter(course=kwargs['course']).count()
        
        return context


class CourseDiscussionQuestionView(TemplateView):
    template_name = 'courses/course_discussion_question.html'

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    @method_decorator(question_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        
        context['comments'] = DiscussionComment.objects.filter(
            question=kwargs['question']).order_by('date_created')

        for comment in context['comments']:
            comment.user_owns_comment = (self.request.user == comment.user)

        return context


class CourseDiscussionQuestionAddView(View):
    template_name = 'courses/course_discussion_question_add.html'

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    def dispatch(self, request, *args, **kwargs):
        kwargs['lessons'] = CourseLesson.objects.filter(
            section__course=kwargs['course'], draft=False)

        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, kwargs)

    def post(self, request, *args, **kwargs):
        kwargs['error'] = None

        title = request.POST.get('title', '')
        content = request.POST.get('content', '')
        lesson = request.POST.get('lesson', '')

        if len(title) < 10 or len(content) < 20:
            kwargs['error'] = _('Title or content are too short.')
        try:
            lesson = CourseLesson.objects.get(id=lesson)
            if not (lesson.section.course == kwargs['course']):
                raise Exception()
        except:
            lesson = None

        if not kwargs['error']:
            DiscussionQuestion(user=request.user, course=kwargs['course'],
                               title=title, content=content,
                               lesson=lesson).save()
            return redirect('courses:course-discussion', slug=kwargs['slug'])

        return render(request, self.template_name, kwargs)


class UserCommentQuestionView(View):

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    @method_decorator(question_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        content = request.POST.get('content', '')

        DiscussionComment(user=request.user,
                          question=kwargs['question'],
                          content=content).save()

        return redirect(kwargs['question'])


class OpenCloseQuestionView(View):

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    @method_decorator(question_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if kwargs['user_owns_question'] or request.user.is_superuser:
            kwargs['question'].is_open = not kwargs['question'].is_open
            kwargs['question'].save()

        return redirect(kwargs['question'])


class DeleteQuestionView(View):

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    @method_decorator(question_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if kwargs['user_owns_question'] or request.user.is_superuser:
            kwargs['question'].delete()

        return redirect('courses:course-discussion', slug=kwargs['slug'])


class DeleteCommentView(View):

    @method_decorator(login_required)
    @method_decorator(course_required)
    @method_decorator(user_enrolled_required)
    def dispatch(self, request, *args, **kwargs):
        return super(self.__class__, self).dispatch(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(DiscussionComment,
            id=request.POST.get('comment_id'))

        if (comment.user == request.user) or request.user.is_superuser:
            comment.delete()

        return redirect('courses:course-discussion', slug=kwargs['slug'])
