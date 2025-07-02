# College Attendance Management System

A comprehensive system for managing student and faculty attendance, built with Django and PostgreSQL.

## Features

-   Role-based access (Admin, Faculty, Student)
-   Bulk attendance marking
-   Leave management with email notifications
-   Dashboards with statistics and charts
-   Export reports to CSV/PDF

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd college_project
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the database:**
    -   Install and run PostgreSQL.
    -   Create a database and a user for the project.

5.  **Configure environment variables:**
    -   Copy `.env.example` to `.env`.
    -   Fill in the values in the `.env` file (SECRET_KEY, DB credentials, etc.).

6.  **Run database migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```
    
7.  **Create a superuser (Admin):**
    ```bash
    python manage.py createsuperuser
    ```
    *After creating, log in to the admin panel and set the user's role to 'ADMIN'.*

8.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
    The application will be available at `http://127.0.0.1:8000`.

## User Guide

-   **Admin**: Log in with your superuser credentials. You can manage all aspects of the system.
-   **Faculty/Student**: An admin must create accounts for faculty and students and assign them the correct role.