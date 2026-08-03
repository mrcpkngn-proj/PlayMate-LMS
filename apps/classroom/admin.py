from django.contrib import admin

from .models import (
    Classroom,
    ClassroomMember,
)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "section",
        "teacher",
        "class_code",
        "is_active",
    )

    search_fields = (
        "name",
        "teacher__username",
        "class_code",
    )


@admin.register(ClassroomMember)
class ClassroomMemberAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "classroom",
        "joined_at",
    )

    search_fields = (
        "student__username",
        "classroom__name",
    )