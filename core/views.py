# core/views.py
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q, F, FloatField
from django.db.models.functions import Cast
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Count
from django.utils import timezone
import io
from django.contrib import messages
from django.db import transaction
import csv
from django.http import HttpResponse, JsonResponse
from django.db.models import Avg, Count, Case, When, Value, IntegerField
from .models import Announcement
from .forms import LeaveRequestForm
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from .chatbot_logic import get_chatbot_response




# core/views.py

from .models import User, StudentProfile, Class, Subject, Attendance, Announcement, LeaveRequest, Timetable, TimeSlot
from .decorators import admin_required, faculty_required, student_required
from .decorators import hod_required

# =================================================================================
# SHARED VIEWS (Used by multiple roles or for redirection)
# =================================================================================


@login_required
def dashboard_redirect(request):
    if request.user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif request.user.role == 'HOD':
        return redirect('hod_dashboard') # <-- NEW REDIRECT
    elif request.user.role == 'FACULTY':
        return redirect('faculty_dashboard')
    else:
        return redirect('student_dashboard')


# =================================================================================
# ADMIN VIEWS
# =================================================================================

class AdminRequiredMixin(LoginRequiredMixin):
    """Ensures that the user is an admin or HOD."""
    def dispatch(self, request, *args, **kwargs):
        allowed_roles = ['ADMIN', 'HOD']
        if not request.user.is_authenticated or request.user.role not in allowed_roles:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


@admin_required
def admin_dashboard(request):
    """
    Displays the main dashboard for the Admin with enhanced summary statistics.
    """
    # --- Stat 1: Calculate Average Attendance (PostgreSQL-compatible) ---

    # We use a Case/When expression to explicitly cast boolean to integer for PostgreSQL.
    average_attendance_agg = Attendance.objects.aggregate(
        avg_present=Avg(
            Case(
                When(is_present=True, then=Value(1)),
                When(is_present=False, then=Value(0)),
                output_field=IntegerField()  # Tell Django the output of this case is an Integer
            )
        )
    )

    # The rest of the logic remains the same
    average_attendance = (average_attendance_agg['avg_present'] * 100) if average_attendance_agg[
                                                                              'avg_present'] is not None else 0

    # --- Stat 2: Calculate Classes Held Today ---
    today = timezone.now().date()
    classes_today = Attendance.objects.filter(date=today).values('subject').distinct().count()
    announcements = Announcement.objects.all()[:5]
    context = {
        'total_students': StudentProfile.objects.count(),
        'total_faculty': User.objects.filter(role='FACULTY').count(),
        'total_courses': Class.objects.count(),
        'total_subjects': Subject.objects.count(),
        'average_attendance': average_attendance,
        'classes_today': classes_today,
        'announcements': announcements,
    }

    return render(request, 'admin/dashboard.html', context)

# core/views.py

# ... existing admin views ...

@admin_required
@transaction.atomic  # Ensures that all student creations in one file succeed or none do
def upload_students_csv(request):
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, "Please select a CSV file to upload.")
            return redirect('admin_student_list')

        csv_file = request.FILES['csv_file']

        # Validate file type
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file. Please upload a valid .csv file.')
            return redirect('admin_student_list')

        # Process the CSV file
        try:
            # We use io.TextIOWrapper to decode the file in memory
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)

            # Skip the header row
            next(reader)

            created_count = 0
            error_count = 0

            for row in reader:
                try:
                    username, password, first_name, last_name, email, roll_no, class_name = row

                    # --- Data Validation ---
                    if User.objects.filter(username=username).exists():
                        messages.warning(request, f"Skipped: User with username '{username}' already exists.")
                        error_count += 1
                        continue

                    if StudentProfile.objects.filter(roll_no=roll_no).exists():
                        messages.warning(request, f"Skipped: Student with roll number '{roll_no}' already exists.")
                        error_count += 1
                        continue

                    # Find the course by its name
                    try:
                        class_obj = Class.objects.get(name__iexact=class_name.strip())
                    except Class.DoesNotExist:
                        messages.warning(request,
                                         f"Skipped: Course '{class_name}' for user '{username}' does not exist.")
                        error_count += 1
                        continue

                    # --- Create User and Profile ---
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        role=User.Role.STUDENT  # Automatically assign the role
                    )

                    StudentProfile.objects.create(
                        user=user,
                        roll_no=roll_no,
                        course=class_obj
                    )
                    created_count += 1

                except ValueError:
                    messages.warning(request, f"Skipped row: {row}. Incorrect number of columns.")
                    error_count += 1
                    continue

            if created_count > 0:
                messages.success(request, f"Successfully added {created_count} new students.")
            if error_count > 0:
                messages.error(request, f"Failed to add {error_count} students. Please check warnings for details.")

        except Exception as e:
            messages.error(request, f"An error occurred while processing the file: {e}")

    return redirect('admin_student_list')


@admin_required
def export_attendance_csv(request):
    """
    Handles the logic for exporting filtered attendance records to a CSV file.
    """
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_records.csv"'

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row
    writer.writerow(['Date', 'Roll No', 'Student Name', 'Course', 'Subject', 'Status', 'Last Updated'])

    # Get the same queryset as the AdminAttendanceView
    queryset = Attendance.objects.select_related('student__user', 'student__course', 'subject').order_by('-date')

    # Apply the same filters from the request GET parameters
    selected_course = request.GET.get('course')
    selected_date = request.GET.get('date')

    if selected_course:
        queryset = queryset.filter(student__course_id=selected_course)
    if selected_date:
        queryset = queryset.filter(date=selected_date)

    # Write data rows
    for record in queryset:
        writer.writerow([
            record.date,
            record.student.roll_no,
            record.student.user.get_full_name(),
            record.student.course.name,
            record.subject.name,
            'Present' if record.is_present else 'Absent',
            record.updated_at.strftime('%Y-%m-%d %H:%M')  # Format the datetime
        ])

    return response


# --- NEW: Reporting Hub View ---
@admin_required
def reports_hub(request):
    """
    A central page that links to all available reports.
    """
    return render(request, 'admin/reports_hub.html')

# admin chatbot views
@admin_required
@require_POST
def admin_chatbot_query(request):
    question = request.POST.get('question', '')

    if not question:
        return JsonResponse({'answer': 'Please ask a question.'})

    # Get the response from our dedicated logic file
    answer = get_chatbot_response(question)

    return JsonResponse({'answer': answer})


@admin_required
def consolidated_report(request):
    """
    Generates a consolidated attendance report for a selected class,
    showing each student's attendance for each subject, and a final summary.
    """
    selected_class_id = request.GET.get('class')
    classes = Class.objects.all().order_by('name')

    # Initialize context with default empty values
    context = {
        'classes': classes,
        'selected_class_id': selected_class_id,
        'report_data': [],
        'subjects_in_course': [],
        'selected_class': None,
        'subject_overall_percentages': {},
        'total_students_in_report': 0,
        'students_above_75': 0,
        'students_below_75': 0,
    }

    if selected_class_id:
        try:
            selected_class = Class.objects.get(pk=selected_class_id)
            context['selected_class'] = selected_class

            students = StudentProfile.objects.filter(course=selected_class).select_related('user').order_by(
                'user__first_name')
            subjects_in_course = Subject.objects.filter(course=selected_class).order_by('name')
            context['subjects_in_course'] = subjects_in_course

            # --- EFFICIENT DATA PRE-FETCHING ---

            # 1. Get total conducted lecture count for each subject.
            lectures_conducted_map = {
                subject.id: Attendance.objects.filter(subject=subject, student__course=selected_class).values('date',
                                                                                                              'time_slot').distinct().count()
                for subject in subjects_in_course
            }

            # 2. Get present counts for each individual student-subject pair.
            present_counts_qs = Attendance.objects.filter(
                student__in=students,
                subject__in=subjects_in_course,
                is_present=True
            ).values('student_id', 'subject_id').annotate(present_count=Count('id'))

            present_counts_map = {(item['student_id'], item['subject_id']): item['present_count'] for item in
                                  present_counts_qs}

            # --- CALCULATE HEADER AVERAGES ---
            subject_percentages = {}
            for subject in subjects_in_course:
                total_present_all = Attendance.objects.filter(subject=subject, student__course=selected_class,
                                                              is_present=True).count()
                total_records_all = Attendance.objects.filter(subject=subject, student__course=selected_class).count()
                percentage = (total_present_all / total_records_all) * 100 if total_records_all > 0 else 0
                subject_percentages[subject.id] = percentage
            context['subject_overall_percentages'] = subject_percentages

            # --- BUILD MAIN REPORT DATA ---
            report_data = []
            for student in students:
                student_data = {'profile': student, 'subject_attendance': [], 'total_attended': 0, 'total_conducted': 0}
                for subject in subjects_in_course:
                    conducted_count = lectures_conducted_map.get(subject.id, 0)
                    present_count = present_counts_map.get((student.id, subject.id), 0)
                    subject_percentage = (present_count / conducted_count) * 100 if conducted_count > 0 else 0

                    student_data['subject_attendance'].append({
                        'attended': present_count,
                        'conducted': conducted_count,
                        'percentage': subject_percentage
                    })
                    student_data['total_attended'] += present_count
                    student_data['total_conducted'] += conducted_count

                student_data['percentage'] = (student_data['total_attended'] / student_data['total_conducted']) * 100 if \
                student_data['total_conducted'] > 0 else 0.0
                report_data.append(student_data)
            context['report_data'] = report_data

            # --- CALCULATE FINAL SUMMARY STATISTICS ---
            total_students_in_report = len(report_data)
            students_above_75 = 0
            students_below_75 = 0

            for data in report_data:
                if data['percentage'] >= 75:
                    students_above_75 += 1
                else:
                    students_below_75 += 1

            context['total_students_in_report'] = total_students_in_report
            context['students_above_75'] = students_above_75
            context['students_below_75'] = students_below_75

        except Class.DoesNotExist:
            messages.error(request, "The selected class does not exist.")

    return render(request, 'admin/consolidated_report.html', context)


@admin_required
@transaction.atomic
def upload_faculty_csv(request):
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, "Please select a CSV file to upload.")
            return redirect('admin_faculty_list')

        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid .csv file.')
            return redirect('admin_faculty_list')

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)

            next(reader)  # Skip header row

            created_count = 0
            error_count = 0

            for row in reader:
                try:
                    # Unpack the columns for a faculty member
                    username, password, first_name, last_name, email = row

                    # --- Data Validation ---
                    if User.objects.filter(username=username).exists():
                        messages.warning(request, f"Skipped: User with username '{username}' already exists.")
                        error_count += 1
                        continue

                    # --- Create User with FACULTY role ---
                    User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        role=User.Role.FACULTY  # Set the role to FACULTY
                    )
                    created_count += 1

                except ValueError:
                    messages.warning(request, f"Skipped row: {row}. Incorrect number of columns. Expected 5.")
                    error_count += 1
                    continue

            if created_count > 0:
                messages.success(request, f"Successfully added {created_count} new faculty members.")
            if error_count > 0:
                messages.info(request,
                              f"Skipped {error_count} rows due to validation errors (e.g., existing username).")

        except Exception as e:
            messages.error(request, f"An error occurred while processing the file: {e}")

    return redirect('admin_faculty_list')


@admin_required
@require_POST  # Ensures this view can only be accessed via a POST request for security
def delete_announcement(request, pk):
    """
    Handles the deletion of a specific announcement.
    """
    try:
        # Find the announcement by its primary key (pk)
        announcement = Announcement.objects.get(pk=pk)
        announcement_title = announcement.title
        announcement.delete()
        messages.success(request, f"The announcement '{announcement_title}' has been deleted successfully.")
    except Announcement.DoesNotExist:
        messages.error(request, "The announcement you tried to delete does not exist.")

    # Redirect back to the admin dashboard where the announcements are listed
    return redirect('admin_dashboard')


@admin_required
def lecture_history_report(request):
    """
    Generates a report showing a history of all lectures for which
    attendance has been taken. Can be filtered by Class.
    """
    # Base queryset: Get distinct combinations of date, time_slot, and subject
    # This represents a unique "lecture session".
    lecture_sessions = Attendance.objects.values(
        'date',
        'time_slot',
        'subject'
    ).distinct().order_by('-date', '-time_slot__start_time')

    # Get the class filter from the request
    selected_class_id = request.GET.get('class')
    selected_class = None

    if selected_class_id:
        try:
            selected_class = Class.objects.get(pk=selected_class_id)
            # Filter the sessions by the selected class
            lecture_sessions = lecture_sessions.filter(subject__course=selected_class)
        except Class.DoesNotExist:
            messages.error(request, "The selected class does not exist.")
            lecture_sessions = Attendance.objects.none()  # Return no results if class is invalid

    # Annotate each session with counts
    # This is a more advanced step that would typically use Subquery, but a loop is clearer here.
    report_data = []

    for session in lecture_sessions:
        subject = Subject.objects.get(pk=session['subject'])
        time_slot = None
        if session['time_slot']:  # Check if the time_slot ID is not None
            try:
                time_slot = TimeSlot.objects.get(pk=session['time_slot'])
            except TimeSlot.DoesNotExist:
                # This case is unlikely but safe to handle
                time_slot = None

                # Get all attendance records for this specific session
        records_for_session = Attendance.objects.filter(
            date=session['date'],
            time_slot_id=session['time_slot'],
            subject_id=session['subject']
        )

        total_students = records_for_session.count()
        present_students = records_for_session.filter(is_present=True).count()

        report_data.append({
            'subject': subject,
            'date': session['date'],
            'time_slot': time_slot,
            'faculty': subject.faculty,
            'total_students': total_students,
            'present_students': present_students
        })

    context = {
        'classes': Class.objects.all().order_by('name'),
        'report_data': report_data,
        'selected_class': selected_class,
    }

    return render(request, 'admin/lecture_history_report.html', context)




# --- NEW: HOD Dashboard View ---
@hod_required
def hod_dashboard(request):
    """
    Displays the main dashboard for the HOD.
    For now, it shows the same system-wide stats as the Admin.
    """
    # This logic is identical to admin_dashboard for now
    average_attendance_agg = Attendance.objects.aggregate(
        avg=Avg(Case(When(is_present=True, then=1), default=0, output_field=IntegerField())))
    average_attendance = (average_attendance_agg['avg'] * 100) if average_attendance_agg['avg'] is not None else 0
    today = timezone.now().date()
    classes_today = Timetable.objects.filter(day_of_week=today.isoweekday()).count()  # A simpler count for now

    context = {
        'total_students': StudentProfile.objects.count(),
        'total_faculty': User.objects.filter(role='FACULTY').count(),
        'total_classes': Class.objects.count(),
        'total_subjects': Subject.objects.count(),
        'average_attendance': average_attendance,
        'classes_today': classes_today,
        'announcements': Announcement.objects.all()[:5],
    }

    return render(request, 'hod/dashboard.html', context)





# --- Management List Views ---

class StudentListView(AdminRequiredMixin, ListView):
    model = StudentProfile
    template_name = 'admin/student_list.html'
    context_object_name = 'students'


class FacultyListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'admin/faculty_list.html'
    context_object_name = 'faculty'
    queryset = User.objects.filter(role='FACULTY')


class CourseListView(AdminRequiredMixin, ListView):
    model = Class
    template_name = 'admin/course_list.html'
    context_object_name = 'courses'


class SubjectListView(AdminRequiredMixin, ListView):
    model = Subject
    template_name = 'admin/subject_list.html'
    context_object_name = 'subjects'


# --- Attendance Management Views ---

class AdminAttendanceView(AdminRequiredMixin, ListView):
    """
    Allows admin to view and filter all attendance records.
    """
    model = Attendance
    template_name = 'admin/attendance_view.html'
    context_object_name = 'attendance_records'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('student__user', 'student__course', 'subject',
                                                         'subject__faculty')

        # --- NEW: Search Logic ---
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            # Search by student's name (first or last) or roll number
            queryset = queryset.filter(
                Q(student__user__first_name__icontains=search_query) |
                Q(student__user__last_name__icontains=search_query) |
                Q(student__roll_no__icontains=search_query)
            )

        # --- Existing and NEW Filtering Logic ---
        selected_date = self.request.GET.get('date')
        selected_course = self.request.GET.get('course')
        selected_subject = self.request.GET.get('subject')  # New
        selected_faculty = self.request.GET.get('faculty')  # New

        if selected_date:
            queryset = queryset.filter(date=selected_date)
        if selected_course:
            queryset = queryset.filter(student__course_id=selected_course)
        if selected_subject:
            queryset = queryset.filter(subject_id=selected_subject)
        if selected_faculty:
            queryset = queryset.filter(subject__faculty_id=selected_faculty)

        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Provide filter options to the template
        context['courses'] = Class.objects.all()
        context['subjects'] = Subject.objects.all()
        context['faculty_list'] = User.objects.filter(role=User.Role.FACULTY)
        return context


class AdminAttendanceUpdateView(AdminRequiredMixin, UpdateView):
    """
    Allows admin to manually edit an attendance record.
    """
    model = Attendance
    fields = ['is_present']
    template_name = 'admin/attendance_edit.html'
    success_url = reverse_lazy('admin_attendance_view')


# --- Reporting Views ---

class LowAttendanceReportView(AdminRequiredMixin, ListView):
    """
    Generates a report of students with attendance below a certain threshold.
    """
    template_name = 'admin/low_attendance_report.html'
    context_object_name = 'students'

    def get_queryset(self):
        threshold = 75.0  # Low attendance threshold percentage

        # This complex query calculates the attendance percentage for each student
        # and filters for those below the threshold.
        students = StudentProfile.objects.annotate(
            total_classes=Count('attendance'),
            present_classes=Count('attendance', filter=Q(attendance__is_present=True))
        ).filter(
            total_classes__gt=0  # Only include students with at least one record
        ).annotate(
            attendance_percentage=Cast(F('present_classes'), FloatField()) * 100 / Cast(F('total_classes'),
                                                                                        FloatField())
        ).filter(
            attendance_percentage__lt=threshold
        ).order_by('attendance_percentage')

        return students


# =================================================================================
# FACULTY VIEWS (Placeholders)
# =================================================================================

@faculty_required
def faculty_dashboard(request):
    """
    Displays a list of subjects, key stats, and the schedule for today.
    """
    faculty_user = request.user

    # Get subjects assigned to this faculty member
    assigned_subjects = Subject.objects.filter(faculty=faculty_user)

    # --- Calculate Dashboard Stats ---
    subject_count = assigned_subjects.count()
    taught_courses = assigned_subjects.values('course').distinct()
    student_count = StudentProfile.objects.filter(course__in=taught_courses).count()

    # --- NEW: Get Today's Schedule for this Faculty ---
    # Get the current day of the week (Monday=1, Sunday=7)
    today_weekday = datetime.today().isoweekday()

    # Fetch timetable entries for today for this faculty's subjects
    todays_schedule = Timetable.objects.filter(
        subject__in=assigned_subjects,
        day_of_week=today_weekday
    ).select_related('subject', 'time_slot', 'subject__course').order_by('time_slot__start_time')

    # --- Fetch Announcements ---
    announcements = Announcement.objects.all()[:5]

    context = {
        'subjects': assigned_subjects,
        'announcements': announcements,
        'subject_count': subject_count,
        'student_count': student_count,
        'todays_schedule': todays_schedule,  # Add schedule to context
    }
    return render(request, 'faculty/dashboard.html', context)




@faculty_required
def take_attendance(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    # SECURITY CHECK:
    if subject.faculty != request.user:
        raise PermissionDenied("You are not authorized to take attendance for this subject.")

    students = StudentProfile.objects.filter(course=subject.course).select_related('user')

    # Get all available time slots to populate the dropdown
    time_slots = TimeSlot.objects.all()

    if request.method == 'POST':
        attendance_date = request.POST.get('attendance_date')
        time_slot_id = request.POST.get('time_slot')  # Get the selected time slot ID
        student_ids = request.POST.getlist('student_ids')

        # Validate that a time slot was selected
        if not time_slot_id:
            messages.error(request, "Please select a time slot.")
            return redirect('faculty_take_attendance', subject_id=subject.id)

        selected_time_slot = get_object_or_404(TimeSlot, pk=time_slot_id)

        for student_id in student_ids:
            student_profile = get_object_or_404(StudentProfile, pk=student_id)
            status = request.POST.get(f'attendance_status_{student_id}')
            is_present = (status == 'present')

            # Use update_or_create, now including the time_slot
            Attendance.objects.update_or_create(
                student=student_profile,
                subject=subject,
                date=attendance_date,
                time_slot=selected_time_slot,  # Pass the selected time slot object
                defaults={'is_present': is_present}
            )

        messages.success(request,
                         f"Attendance for {subject.name} on {attendance_date} at {selected_time_slot} has been saved.")
        return redirect('faculty_dashboard')

    context = {
        'subject': subject,
        'students': students,
        'time_slots': time_slots,  # Pass time slots to the template
        'today': timezone.now(),  # Pass today's date for the form default
    }
    return render(request, 'faculty/take_attendance.html', context)


@faculty_required
def view_class_attendance(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)

    # SECURITY CHECK:
    if subject.faculty != request.user:
        raise PermissionDenied("You are not authorized to view this data.")

    # --- 1. Calculate Student Insights (Attendance Percentages) ---
    students_in_course = StudentProfile.objects.filter(course=subject.course).select_related('user')

    student_insights = []
    for student_profile in students_in_course:
        # Get total classes for THIS subject for this student
        total_classes = Attendance.objects.filter(subject=subject, student=student_profile).count()
        # Get present classes for THIS subject for this student
        present_classes = Attendance.objects.filter(subject=subject, student=student_profile, is_present=True).count()

        if total_classes > 0:
            percentage = (present_classes / total_classes) * 100
        else:
            percentage = 100  # Default to 100 if no classes held/marked yet

        student_insights.append({
            'profile': student_profile,
            'percentage': percentage,
            'total_classes': total_classes,
            'present_classes': present_classes,
        })

    # --- 2. Get Detailed Records (for the table below) ---
    queryset = Attendance.objects.filter(subject=subject).select_related('student__user').order_by('-date',
                                                                                                   'student__user__first_name')

    # Apply student filter if one is selected
    selected_student_id = request.GET.get('student')
    if selected_student_id:
        queryset = queryset.filter(student_id=selected_student_id)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        queryset = queryset.filter(date__range=[start_date, end_date])

    context = {
        'subject': subject,
        'student_insights': student_insights,  # NEW: Pass insights to template
        'records': queryset,
        'students_in_course': students_in_course,  # For the filter dropdown
    }
    return render(request, 'faculty/view_attendance.html', context)

@faculty_required
def edit_attendance(request, attendance_id):
    attendance_record = get_object_or_404(Attendance, pk=attendance_id)

    # SECURITY CHECK: Ensure faculty owns the subject of the attendance record.
    if attendance_record.subject.faculty != request.user:
        raise PermissionDenied("You are not authorized to edit this record.")

    # SECURITY CHECK: Implement the 24-hour editing window.
    time_since_update = timezone.now() - attendance_record.updated_at
    if time_since_update > timedelta(hours=24):
        messages.error(request, "This attendance record is more than 24 hours old and can no longer be edited.")
        return redirect('faculty_view_attendance', subject_id=attendance_record.subject.id)

    if request.method == 'POST':
        status = request.POST.get('status')
        attendance_record.is_present = (status == 'present')
        attendance_record.save()
        messages.success(request, "Attendance record updated successfully.")
        return redirect('faculty_view_attendance', subject_id=attendance_record.subject.id)

    context = {
        'record': attendance_record
    }
    return render(request, 'faculty/edit_attendance.html', context)


@faculty_required
def faculty_timetable(request):
    faculty_user = request.user
    timetable_entries = Timetable.objects.filter(
        subject__faculty=faculty_user
    ).select_related('subject', 'time_slot').order_by('day_of_week', 'time_slot__start_time')

    context = {
        'timetable_entries': timetable_entries,
        'days': Timetable.DAY_CHOICES,
    }
    return render(request, 'faculty/timetable.html', context)

# =================================================================================
# STUDENT VIEWS (Placeholders)
# =================================================================================

@student_required
def student_dashboard(request):
    # This view would show student-specific information
    student = request.user.student_profile
    total_classes = Attendance.objects.filter(student=student).count()
    present_count = Attendance.objects.filter(student=student, is_present=True).count()
    absent_count = total_classes - present_count

    attendance_percentage = (present_count / total_classes) * 100 if total_classes > 0 else 0
    announcements = Announcement.objects.all()[:5]
    context = {
        'total_classes': total_classes,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': attendance_percentage,
        'announcements': announcements,
    }
    return render(request, 'student/dashboard.html', context)


# core/views.py

@student_required
def student_attendance_report(request):
    """
    Generates a consolidated, subject-wise attendance report for the logged-in student.
    """
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        return render(request, 'student/no_profile.html')

    # Get all subjects for the student's class
    subjects_in_course = Subject.objects.filter(course=student_profile.course).order_by('name')

    # Pre-fetch total conducted lectures for each subject to be efficient
    lectures_conducted_map = {
        subject.id: Attendance.objects.filter(subject=subject).values('date', 'time_slot').distinct().count()
        for subject in subjects_in_course
    }

    # Pre-fetch all of the student's 'present' attendance records at once
    present_counts_qs = Attendance.objects.filter(
        student=student_profile,
        is_present=True
    ).values('subject_id').annotate(present_count=Count('id'))

    present_counts_map = {item['subject_id']: item['present_count'] for item in present_counts_qs}

    # --- Build the report data ---
    report_data = []
    total_attended_overall = 0
    total_conducted_overall = 0

    for subject in subjects_in_course:
        conducted_count = lectures_conducted_map.get(subject.id, 0)
        present_count = present_counts_map.get(subject.id, 0)

        percentage = (present_count / conducted_count) * 100 if conducted_count > 0 else 0.0

        report_data.append({
            'subject_name': subject.name,
            'attended': present_count,
            'conducted': conducted_count,
            'percentage': percentage,
        })

        total_attended_overall += present_count
        total_conducted_overall += conducted_count

    # Calculate final overall percentage
    overall_percentage = (
                                     total_attended_overall / total_conducted_overall) * 100 if total_conducted_overall > 0 else 0.0

    context = {
        'report_data': report_data,
        'overall_attended': total_attended_overall,
        'overall_conducted': total_conducted_overall,
        'overall_percentage': overall_percentage,
    }

    return render(request, 'student/attendance_report.html', context)


@student_required
def student_attendance_history(request):
    """
    Fetches and displays a simple, chronological list of all attendance
    records for the logged-in student.
    """
    try:
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        # This handles the edge case where a student user has no profile
        # You can create a simple 'no_profile.html' template to show an error
        return render(request, 'student/no_profile.html')

    # Fetch all records for this student, ordered by most recent date and time
    attendance_records = Attendance.objects.filter(
        student=student_profile
    ).select_related('subject', 'time_slot').order_by('-date', '-time_slot__start_time')

    context = {
        'attendance_records': attendance_records,
    }

    return render(request, 'student/attendance_history.html', context)
# --- NEW Student Timetable View ---
@student_required
def student_timetable(request):
    """
    Displays the full weekly timetable for the logged-in student's course.
    This version passes an ordered list of entries and a list of days,
    which is simpler and more robust for template rendering.
    """
    try:
        # Get the profile of the logged-in student
        student_profile = request.user.student_profile
    except StudentProfile.DoesNotExist:
        # Handle the edge case where a student user has no profile
        # You can redirect or show an error message
        return render(request, 'student/no_profile.html')

    # Fetch all timetable entries for subjects in the student's course
    timetable_entries = Timetable.objects.filter(
        subject__course=student_profile.course
    ).select_related(
        'subject',
        'time_slot',
        'subject__faculty'
    ).order_by('day_of_week', 'time_slot__start_time')

    context = {
        'timetable_entries': timetable_entries,
        'days': Timetable.DAY_CHOICES,  # Pass the choices directly: [(1, 'Monday'), (2, 'Tuesday'), ...]
        'student_course': student_profile.course,
    }

    return render(request, 'student/timetable.html', context)
# --- A. NEW EMAIL HELPER FUNCTION ---
def send_leave_status_email(leave_request):
    """Helper function to send email notification for leave status update."""
    subject = f"Update on your Leave Request"
    status_text = leave_request.get_status_display()  # Gets the human-readable status like "Approved"
    message = (
        f"Dear {leave_request.user.get_full_name()},\n\n"
        f"The status of your leave request from {leave_request.start_date} to {leave_request.end_date} has been updated.\n\n"
        f"New Status: {status_text}\n\n"
        f"Thank you,\n"
        f"College Administration"
    )
    # Ensure you have EMAIL_HOST_USER set in your .env/settings
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [leave_request.user.email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as e:
        # For now, we'll just print the error if email fails.
        # In a production app, you'd want to log this properly.
        print(f"Error sending email: {e}")


# --- B. NEW ADMIN VIEWS ---
class LeaveRequestListView(AdminRequiredMixin, ListView):
    model = LeaveRequest
    template_name = 'admin/leave_request_list.html'
    context_object_name = 'leave_requests'
    ordering = ['-created_at']  # Show newest requests first


@admin_required
def update_leave_request_status(request, pk, status):
    if request.method == 'POST':
        leave_request = get_object_or_404(LeaveRequest, pk=pk)

        if status in ['APPROVED', 'REJECTED']:
            leave_request.status = status
            leave_request.save()

            # Send email notification
            send_leave_status_email(leave_request)

            messages.success(request, f"Leave request has been {status.lower()}.")
        else:
            messages.error(request, "Invalid status.")

    return redirect('admin_leave_request_list')


# --- C. NEW SHARED VIEW FOR APPLYING ---
@login_required
def apply_for_leave(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.user = request.user  # Assign the logged-in user
            leave_request.save()
            messages.success(request, 'Your leave request has been submitted successfully!')
            return redirect('dashboard_redirect')  # Redirect to their own dashboard
    else:
        form = LeaveRequestForm()

    return render(request, 'leave/apply_for_leave.html', {'form': form})






