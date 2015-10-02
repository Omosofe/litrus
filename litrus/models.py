# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from litrus.signals import *


LANGUAGES = [
    ('af', 'Afrikaans'),
    ('nl', 'Nederlands'),
    ('en', 'English'),
    ('fr', 'Français'),
    ('gl', 'Galego'),
    ('de', 'Deutsch'),
    ('it', 'Italiano'),
    ('jp', '日本語'),
    ('pl', 'Polski'),
    ('pt', 'Português'),
    ('ru', 'Русский'),
    ('es', 'Español'),
]

LEVELS = [
    (1, _('Beginner')),
    (2, _('Intermediate')),
    (3, _('Expert')),
    (0, _('All Levels')),
]


class CourseCategory(models.Model):

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text='Url friendly name for the category. Example: http://example.com/courses/?category=<b>your-slug</b>')

    class Meta:
        ordering = ['name']
        verbose_name = 'Course Category'
        verbose_name_plural = 'Course Categories'

    def __str__(self):
        return u'{0}'.format(self.name)

    def __unicode__(self):
        return self.__str__()

    def get_absolute_url(self):
        url = reverse_lazy('courses:courses') + '?category=' + self.slug
        return url


class Course(models.Model):

    draft = models.BooleanField(default=True, help_text='Check this if you <b>DO NOT</b> want to make the course available to users.')
    public = models.BooleanField(default=True, help_text='If checked your users <b>DO NOT</b> need to be subscribed to take the course.')
    slug = models.SlugField(unique=True, help_text='Url friendly name for the course. Example: http://example.com/courses/<b>your-slug</b>/')
    name = models.CharField(max_length=100)
    category = models.ForeignKey(CourseCategory)
    video = models.FileField(upload_to='videos/courses', blank=True, default='')
    logo = models.FileField(upload_to='images/courses', blank=True, default='')
    language = models.CharField(max_length=10, choices=LANGUAGES)
    level = models.PositiveSmallIntegerField(choices=LEVELS)
    short_description = models.TextField()
    description = models.TextField(help_text='You <b>CAN</b> use Markdown here.')
    requirements = models.TextField()
    target = models.TextField()

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return u'{0} | {1}{2}'.format(self.category.name, self.slug,
                                  ' [DRAFT]' if self.draft else '')

    def __unicode__(self):
        return self.__str__()

    def clean(self):
        if len(self.short_description) > 200:
            raise ValidationError('Short description must NOT exceed 200 characters.')

    def get_absolute_url(self):
        return reverse_lazy('courses:course', kwargs={ 'slug': self.slug })

    def get_dashboard_url(self):
        return reverse_lazy('courses:course-dashboard',
            kwargs={ 'slug': self.slug })

    def get_lesson_url(self, lesson_id):
        return reverse_lazy('courses:course-lesson',
            kwargs={ 'slug': self.slug, 'lesson_id': lesson_id })

    @property
    def sections(self):
        return CourseSection.objects.filter(course=self).order_by('number')

    @property
    def verbose_language(self):
        return dict(LANGUAGES).get(self.language, '')

    @property
    def verbose_level(self):
        return dict(LEVELS).get(self.level, '')

    @classmethod
    def of_user(cls, user):
        enrollments = CourseEnrollment.objects.filter(user=user)
        return [ e.course for e in enrollments ]

    def lessons(self):
        """
        List of lessons ids for the course.
        """
        lessons = CourseLesson.objects.filter(
            section__course=self, draft=False).values_list('id')

        lessons = [ e[0] for e in lessons ]

        return lessons

    def lessons_taken(self, user):
        """
        List of lessons ids completed by `user` for the course.
        """
        lessons_taken = UserLesson.objects.filter(
            user=user, lesson__section__course=self,
            lesson__draft=False).values_list('lesson_id')
        
        lessons_taken = [ e[0] for e in lessons_taken ]

        return lessons_taken

    def percentage_completed_of_user(self, user):
        lessons_taken = self.lessons_taken(user)
        lessons = self.lessons()
        try:
            completed = int((len(lessons_taken) /
                        float(len(lessons))) * 100)
        except ZeroDivisionError:
            completed = 0

        return (lessons, lessons_taken, completed)


class CourseSection(models.Model):

    course = models.ForeignKey(Course)
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['name', 'number']
        verbose_name = 'Course Section'
        verbose_name_plural = 'Course Sections'

    def __str__(self):
        return u'{0} | {1} {2}'.format(self.course.slug, self.number, self.name)

    def __unicode__(self):
        return self.__str__()

    def clean(self):
        if self.number <= 0:
            raise ValidationError('Section number can not be cero or negative.')
        sections = CourseSection.objects.filter(course=self.course,
                                                number=self.number)
        if sections:
            raise ValidationError('Section number already exists for this course.')

    @property
    def lessons(self):
        return CourseLesson.objects.filter(section=self).order_by('number')


class CourseLesson(models.Model):

    draft = models.BooleanField(default=True, help_text='Check this if you <b>DO NOT</b> want to make the lesson available to users.')
    section = models.ForeignKey(CourseSection)
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    video = models.FileField(upload_to='videos/lessons', blank=True, default='')
    content = models.TextField(blank=True, default='')
    date_edited = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['section', 'number']
        verbose_name = 'Course Lesson'
        verbose_name_plural = 'Course Lessons'

    def __str__(self):
        return u'{0} | {1}.{2} {3}{4}'.format(self.section.course.slug,
                                              self.section.number,
                                              self.number, self.name,
                                              ' [DRAFT]' if self.draft else '')

    def __unicode__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse_lazy('courses:course-lesson',
            kwargs={ 'slug': self.section.course.slug,
                     'lesson_id': self.id })

    def clean(self):
        if self.number <= 0:
            raise ValidationError('Lesson number can not be cero or negative.')
        lessons = CourseLesson.objects.filter(section=self.section,
                                              number=self.number)
        if lessons:
            if not (lessons[0].id == self.id):
                raise ValidationError(
                        'Lesson number already exists for this course section.')

        if not self.draft:
            if not self.video and not self.content:
                raise ValidationError(
                        'Add video or content before making lesson visible.')


class CourseEnrollment(models.Model):

    user = models.ForeignKey(User)
    course = models.ForeignKey(Course)
    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Course Enrollment'
        verbose_name_plural = 'Course Enrollments'

    def __str__(self):
        return u'{0} | {1} | {2}'.format(
            self.user.username, self.course.slug,
            self.date_enrolled.strftime('%b %d, %Y'))

    def __unicode__(self):
        return self.__str__()


class Subscription(models.Model):

    user = models.OneToOneField(User, related_name='subscription')
    date_subscribed = models.DateTimeField(auto_now=True)
    date_expiration = models.DateTimeField()

    class Meta:
        verbose_name = 'User Subscription'
        verbose_name_plural = 'User Subscriptions'

    def __str__(self):
        return u'{0} | Subscribed {1} | Expires {2}'.format(
            self.user.username, self.date_subscribed.strftime('%b %d, %Y'),
            self.date_expiration.strftime('%b %d, %Y'))

    def __unicode__(self):
        return self.__str__()

    def has_expired(self):
        return bool(timezone.now() > self.date_expiration)


class SubscriptionPlan(models.Model):

    level = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    months = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2, help_text='For example: 19.99 or 120.00')

    class Meta:
        ordering = ['level']
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return u'{0} | {1} | ${2} For {3} Months'.format(
            self.level, self.name, self.price, self.months)

    def __unicode__(self):
        return self.__str__()

    def clean(self):
        if self.level <= 0:
            raise ValidationError('Level must be positive and not zero.')
        if self.months <= 0:
            raise ValidationError('Enter at least 1 month or more.')
        if self.price <= 0:
            raise ValidationError('Price must be positive and not zero.')


class UserLesson(models.Model):

    user = models.ForeignKey(User)
    lesson = models.ForeignKey(CourseLesson)
    date_started = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')
        verbose_name = 'User lesson'
        verbose_name_plural = 'User lessons'

    def __str__(self):
        return u'{0} takes lesson {1}'.format(
            self.user.username, self.lesson.id)

    def __unicode__(self):
        return self.__str__()


class DiscussionQuestion(models.Model):

    user = models.ForeignKey(User)
    course = models.ForeignKey(Course)
    lesson = models.ForeignKey(CourseLesson, null=True)
    title = models.CharField(max_length=150)
    content = models.TextField(blank=True, default='')
    is_open = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'On {0} | {1}'.format(self.course.slug, self.title)

    def __unicode__(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse_lazy('courses:course-discussion-question',
            kwargs={ 'slug': self.course.slug, 'question_id': self.id })


class DiscussionComment(models.Model):

    user = models.ForeignKey(User)
    question = models.ForeignKey(DiscussionQuestion)
    content = models.TextField(blank=True, default='')
    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)

    def __str__(self):
        return u'On {0} | By {1}'.format(self.question.course.slug,
                                        self.user.username)

    def __unicode__(self):
        return self.__str__()


class PasswordResetToken(models.Model):

    user = models.OneToOneField(User)
    token = models.CharField(max_length=150)
    date_sent = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Password Token'
        verbose_name_plural = 'Password Tokens'

    def __str__(self):
        return u'On {0} | By {1}'.format(self.date_sent.strftime('%b %d, %Y'),
                                        self.user.username)

    def __unicode__(self):
        return self.__str__()

    def get_absolute_url(self):
        url = reverse_lazy('accounts:password-reset') + '?token=' + self.token
        return url


class EmailValidationToken(models.Model):

    user = models.OneToOneField(User)
    token = models.CharField(max_length=150)
    date_sent = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Email Validation Token'
        verbose_name_plural = 'Email Validation Tokens'

    def __str__(self):
        return u'On {0} | By {1}'.format(self.date_sent.strftime('%b %d, %Y'),
                                        self.user.username)

    def __unicode__(self):
        return self.__str__()

    def get_absolute_url(self):
        url = reverse_lazy('accounts:email-validation') + '?token=' + self.token
        return url
