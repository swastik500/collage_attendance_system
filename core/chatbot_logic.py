# core/chatbot_logic.py

import re
from django.db.models import Avg, Count, Case, When, Value, IntegerField, Q, F
from .models import User, StudentProfile, Attendance  # Import necessary models


# --- 1. Define Helper Functions (The Chatbot's "Skills") ---

def handle_count_students():
    count = StudentProfile.objects.count()
    return f"There are currently {count} students registered in the system."


def handle_count_faculty():
    count = User.objects.filter(role=User.Role.FACULTY).count()
    return f"There are {count} faculty members in the system."


def handle_average_attendance():
    agg = Attendance.objects.aggregate(
        avg=Avg(Case(When(is_present=True, then=1), default=0, output_field=IntegerField())))
    avg_percent = (agg['avg'] * 100) if agg['avg'] is not None else 0
    return f"The overall average attendance is {avg_percent:.2f}%."


def handle_low_attendance_students():
    threshold = 75.0
    students = StudentProfile.objects.annotate(
        present_count=Count('attendance', filter=Q(attendance__is_present=True)),
        total_classes=Count('attendance')
    ).filter(total_classes__gt=0).annotate(
        percentage=F('present_count') * 100.0 / F('total_classes')
    ).filter(percentage__lt=threshold)

    if not students.exists():
        return "Great news! No students currently have low attendance."

    student_list = "\n".join([f"- {s.user.get_full_name()} ({s.percentage:.1f}%)" for s in students])
    return f"Here are the students with low attendance (<{threshold}%):\n{student_list}"


# --- 2. Define the Main Handler Function ---

def get_chatbot_response(question: str) -> str:
    """
    This is the main entry point for the chatbot.
    It takes a question, matches it against patterns, and returns a response string.
    """
    question = question.lower().strip()

    # Each tuple is (regex_pattern, handler_function_to_call)
    intent_patterns = [
        (r'how many students', handle_count_students),
        (r'count students', handle_count_students),
        (r'how many faculty|how many teachers|count faculty|count teachers', handle_count_faculty),
        (r'average attendance|overall attendance', handle_average_attendance),
        (r'low attendance|who has low attendance', handle_low_attendance_students),
        # Add more patterns here in the future...
    ]

    # Find the first matching pattern and execute its handler
    for pattern, handler in intent_patterns:
        if re.search(pattern, question):
            try:
                # Call the matched handler function and return its result
                return handler()
            except Exception as e:
                # In case of an unexpected error in the handler function
                return f"I encountered an error trying to answer that: {e}"

    # If no patterns match, return the default fallback response
    return "I'm sorry, I don't understand that question. Try asking about student counts, faculty counts, or low attendance."