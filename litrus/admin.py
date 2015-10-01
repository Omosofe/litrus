from django.contrib import admin

from litrus.models import *


admin.site.register(CourseCategory)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    fieldsets = (
        (None, {
            'fields': ('draft', 'public', 'name', 'slug', 'language', 'category', 'level'),
        }),
        ('Media', {
            'fields': ('logo', 'video'),
        }),
        ('Content', {
            'fields': ('short_description', 'description', 'requirements', 'target'),
        }),
    )
    list_filter = ['draft', 'public']
    search_fields = ['name', 'slug']


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):

    search_fields = ['name', 'course__name', 'course__slug']


@admin.register(CourseLesson)
class CourseLessonAdmin(admin.ModelAdmin):

    list_filter = ['draft']
    search_fields = ['name']


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):

    raw_id_fields = ['user']
    readonly_fields = ['date_enrolled']
    search_fields = ['user__username', 'course__name']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):

    raw_id_fields = ['user']
    search_fields = ['user__username']


admin.site.register(SubscriptionPlan)


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):

    raw_id_fields = ['user']
    readonly_fields = ['date_sent']


@admin.register(EmailValidationToken)
class EmailValidationAdmin(admin.ModelAdmin):

    raw_id_fields = ['user']
    readonly_fields = ['date_sent']
