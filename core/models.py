from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager


# =================================================================================
# Custom User Model and Managers
# =================================================================================

class User(AbstractUser):
    """
    Custom User model to include a 'role' for access control.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STUDENT = "STUDENT", "Student"
        FACULTY = "FACULTY", "Faculty"

    # The role field is mandatory and has no default.
    # It must be set explicitly when a user is created.
    role = models.CharField(max_length=50, choices=Role.choices)


class StudentManager(BaseUserManager):
    """
    Custom manager for the Student proxy model.
    It filters the queryset to only include users with the 'STUDENT' role.
    """

    def get_queryset(self, *args, **kwargs):
        # Call the parent's get_queryset first, then apply our filter.
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.STUDENT)


class FacultyManager(BaseUserManager):
    """
    Custom manager for the Faculty proxy model.
    It filters the queryset to only include users with the 'FACULTY' role.
    """

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(role=User.Role.FACULTY)


# =================================================================================
# Proxy Models for Role-Based Management
# =================================================================================

class Student(User):
    """
    Proxy model for Users with the 'STUDENT' role.
    Allows for separate admin interface and role-specific methods.
    """
    objects = StudentManager()

    class Meta:
        proxy = True  # This makes it a proxy model

    def save(self, *args, **kwargs):
        if not self.pk:  # When creating a new student
            self.role = User.Role.STUDENT
        return super().save(*args, **kwargs)

    def welcome(self):
        return "Only for students"


class Faculty(User):
    """
    Proxy model for Users with the 'FACULTY' role.
    """
    objects = FacultyManager()

    class Meta:
        proxy = True

    def save(self, *args, **kwargs):
        if not self.pk:  # When creating a new faculty member
            self.role = User.Role.FACULTY
        return super().save(*args, **kwargs)

    def welcome(self):
        return "Only for faculty"


# =================================================================================
# Academic Structure Models
# =================================================================================

class Department(models.Model):
    """
    Represents an academic department, e.g., 'Computer Science'.
    """
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Class(models.Model):
    name = models.CharField(max_length=120, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classes')

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    course = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='subjects')
    faculty = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                limit_choices_to={'role': User.Role.FACULTY})

    def __str__(self):
        return f"{self.name} ({self.course.name})"


# =================================================================================
# Profile and Transactional Models
# =================================================================================

class StudentProfile(models.Model):
    """
    Holds extra information specific to a student user.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile',
                                limit_choices_to={'role': User.Role.STUDENT})
    roll_no = models.CharField(max_length=20, unique=True)
    course = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='students')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.roll_no})"


class Attendance(models.Model):
    """
    Stores a single attendance record for a student in a subject on a specific date.
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate entries for the same student, subject, and date.
        unique_together = ('student', 'subject', 'date')

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student} - {self.subject.name} on {self.date} [{status}]"


class LeaveRequest(models.Model):
    """
    Stores leave requests from both students and faculty.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Leave request by {self.user.username} - {self.status}"

# =================================================================================
# Announcement Model
# =================================================================================

class Announcement(models.Model):
    """
    Represents an announcement posted by an Admin for all users to see.
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': User.Role.ADMIN})
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # Show the newest announcements first

    def __str__(self):
        return self.title


class TimeSlot(models.Model):
    """
    Represents a single time slot in a day, e.g., '9:00 AM - 10:00 AM'.
    """
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"

    class Meta:
        ordering = ['start_time']


class Timetable(models.Model):
    """
    Links a Subject to a specific day of the week and a TimeSlot.
    This forms one entry in the weekly schedule.
    """
    DAY_CHOICES = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)

    class Meta:
        # Prevent scheduling the same subject at the exact same time on the same day
        unique_together = ('subject', 'day_of_week', 'time_slot')

    def __str__(self):
        return f"{self.subject} on {self.get_day_of_week_display()} at {self.time_slot}"