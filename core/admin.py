# core/admin.py (NEW & IMPROVED)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, Class, Subject, StudentProfile, Attendance, LeaveRequest, Student, Faculty
from .models import Announcement
from .models import TimeSlot, Timetable



# --- Student Admin ---
@admin.register(Student)
class StudentAdmin(UserAdmin):
    # This is where the magic happens. We override save_model.
    def save_model(self, request, obj, form, change):
        # When creating a new student through this admin, set their role automatically.
        if not change:  # 'change' is False when creating a new object
            obj.role = User.Role.STUDENT
        super().save_model(request, obj, form, change)

    # We can customize the fields shown in the list view
    list_display = ('username', 'first_name', 'last_name', 'email')

    # We only want to see users with the STUDENT role in this admin view.
    def get_queryset(self, request):
        return User.objects.filter(role=User.Role.STUDENT)


# --- Faculty Admin ---
@admin.register(Faculty)
class FacultyAdmin(UserAdmin):
    def save_model(self, request, obj, form, change):
        if not change:
            obj.role = User.Role.FACULTY
        super().save_model(request, obj, form, change)

    list_display = ('username', 'first_name', 'last_name', 'email')

    def get_queryset(self, request):
        return User.objects.filter(role=User.Role.FACULTY)


# --- Register other models as before ---
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'faculty')
    list_filter = ('course', 'faculty')

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted_by', 'created_at')
    list_filter = ('created_at', 'posted_by')
    search_fields = ('title', 'content')

    # Automatically set the 'posted_by' field to the current user
    def save_model(self, request, obj, form, change):
        if not obj.posted_by_id:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('subject', 'day_of_week', 'time_slot', 'get_faculty')
    list_filter = ('day_of_week', 'subject__course', 'subject__faculty')
    search_fields = ('subject__name',)

    @admin.display(description='Faculty')
    def get_faculty(self, obj):
        return obj.subject.faculty


admin.site.register(TimeSlot)

admin.site.register(Department)
admin.site.register(Class)
admin.site.register(Attendance)
admin.site.register(LeaveRequest)
admin.site.register(StudentProfile)

# We no longer need a custom User admin, as management is handled
# by the more specific StudentAdmin and FacultyAdmin.
# The default admin site will still allow superusers to see all users if needed.