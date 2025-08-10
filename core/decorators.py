# core/decorators.py
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

def student_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a student.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'STUDENT',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def faculty_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    '''
    Decorator for views that checks that the logged in user is a faculty member.
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'FACULTY',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'ADMIN',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function: return actual_decorator(function)
    return actual_decorator

# --- Create hod_required ---
def hod_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    """
    Decorator for views that checks that the user is an HOD.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.role == 'HOD',
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function: return actual_decorator(function)
    return actual_decorator
