from django.conf.urls import include, url

from litrus.modules.courses.views import *


urlpatterns = [
    url(r'^$', CoursesView.as_view(), name='courses'),
    url(r'^user/enrollment/$', CourseEnrollmentView.as_view(), name='course-enrollment'),
    url(r'^(?P<slug>[-\w]+)/$', CourseView.as_view(), name='course'),
    url(r'^(?P<slug>[-\w]+)/dashboard/$', CourseDashboardView.as_view(), name='course-dashboard'),
    url(r'^(?P<slug>[-\w]+)/lesson/(?P<lesson_id>[-\w]+)$', CourseLessonView.as_view(), name='course-lesson'),
    url(r'^user/finish/lesson/$', UserFinishLessonView.as_view(), name='user-finish-lesson'),
    url(r'^(?P<slug>[-\w]+)/discussion/$', CourseDiscussionView.as_view(), name='course-discussion'),
    url(r'^(?P<slug>[-\w]+)/discussion/question/(?P<question_id>[-\w]+)$', CourseDiscussionQuestionView.as_view(), name='course-discussion-question'),
    url(r'^(?P<slug>[-\w]+)/discussion/question/add/(?:/(?P<question_id>[-\w]+)/)?$', CourseDiscussionQuestionAddView.as_view(), name='course-discussion-question-add'),
    url(r'^(?P<slug>[-\w]+)/user/comment/question/(?P<question_id>[-\w]+)$', UserCommentQuestionView.as_view(), name='user-comment-question'),
    url(r'^(?P<slug>[-\w]+)/openclose/question/(?P<question_id>[-\w]+)$', OpenCloseQuestionView.as_view(), name='open-close-question'),
    url(r'^(?P<slug>[-\w]+)/delete/question/(?P<question_id>[-\w]+)$', DeleteQuestionView.as_view(), name='delete-question'),
    url(r'^(?P<slug>[-\w]+)/delete/comment/$', DeleteCommentView.as_view(), name='delete-comment'),
]
