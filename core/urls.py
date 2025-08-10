# core/urls.py


from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login-explicit'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('password_reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),


    # Main Dashboard Redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    # =================================================================================
    # ADMIN URLS (Corrected Paths)
    # =================================================================================
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('admin_chatbot_query/', views.admin_chatbot_query, name='admin_chatbot_query'),

    # NEW - Announcement Management
    path('admin_announcement/delete/<int:pk>/', views.delete_announcement, name='admin_announcement_delete'),

    # User Management
    path('admin_students/', views.StudentListView.as_view(), name='admin_student_list'),
    path('admin_students/upload/', views.upload_students_csv, name='admin_student_upload_csv'),
    path('admin_faculty/', views.FacultyListView.as_view(), name='admin_faculty_list'),
    path('admin_faculty/upload/', views.upload_faculty_csv, name='admin_faculty_upload_csv'),

    # Academic Management
    path('admin_courses/', views.CourseListView.as_view(), name='admin_course_list'),
    path('admin_subjects/', views.SubjectListView.as_view(), name='admin_subject_list'),

    # Attendance Management
    path('admin_attendance/', views.AdminAttendanceView.as_view(), name='admin_attendance_view'),
    path('admin_attendance/export/', views.export_attendance_csv, name='admin_attendance_export_csv'),
    path('admin_attendance/edit/<int:pk>/', views.AdminAttendanceUpdateView.as_view(), name='admin_attendance_edit'),

    # Reporting
    path('admin_reports/', views.reports_hub, name='admin_reports_hub'),
    path('admin_reports/low_attendance/', views.LowAttendanceReportView.as_view(), name='admin_low_attendance_report'),
    #path('admin_reports/low_attendance/pdf/', views.export_low_attendance_pdf, name='admin_low_attendance_report_pdf'),
    path('admin_reports/consolidated/', views.consolidated_report, name='admin_consolidated_report'),
    path('admin_reports/lecture_history/', views.lecture_history_report, name='admin_lecture_history_report'),



    # NEW - Leave Management
    path('admin_leave_requests/', views.LeaveRequestListView.as_view(), name='admin_leave_request_list'),
    path('admin_leave_requests/update/<int:pk>/<str:status>/', views.update_leave_request_status,
         name='admin_update_leave_status'),

    # =================================================================================
    # HOD URLS (NEW SECTION)
    # =================================================================================
    path('hod/dashboard/', views.hod_dashboard, name='hod_dashboard'),
    # =================================================================================
    # FACULTY & STUDENT URLS
    # =================================================================================
    # core/urls.py

    # ... (keep admin and auth urls as they are) ...

    # =================================================================================
    # FACULTY & STUDENT URLS
    # =================================================================================

    # --- Faculty URLs ---

    path('faculty_dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/timetable/', views.faculty_timetable, name='faculty_timetable'),
    path('faculty/attendance/take/<int:subject_id>/', views.take_attendance, name='faculty_take_attendance'),
    path('faculty/attendance/view/<int:subject_id>/', views.view_class_attendance, name='faculty_view_attendance'),
    path('faculty/attendance/edit/<int:attendance_id>/', views.edit_attendance, name='faculty_edit_attendance'),
    # NEW - Apply for Leave (a shared URL for both roles)
    path('leave/apply/', views.apply_for_leave, name='apply_for_leave'),
     # ... other faculty and student urls

    # --- Student URLs ---
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/timetable/', views.student_timetable, name='student_timetable'),
    path('student_attendance_report/', views.student_attendance_report, name='student_attendance_report'),
    path('student/history/', views.student_attendance_history, name='student_attendance_history'),
]