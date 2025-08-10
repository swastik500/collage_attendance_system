# College Attendance Management System

A comprehensive web-based system for managing student and faculty attendance in educational institutions, built with modern web technologies and featuring role-based access control, automated reporting, and intelligent chatbot assistance.

## 🚀 Technologies Used

### Backend Framework
- **Django 5.2.3** - High-level Python web framework
  - MVT (Model-View-Template) architecture
  - Built-in ORM for database operations
  - Admin interface for system administration
  - User authentication and authorization system

### Database
- **PostgreSQL** - Advanced open-source relational database
  - Connected via `psycopg2-binary` adapter
  - ACID compliance for data integrity
  - Complex query support for attendance analytics

### Frontend Technologies
- **HTML5** - Semantic markup with Django templates
- **CSS3 & Bootstrap 4** - Responsive design and styling
- **JavaScript** - Interactive user interface elements
- **Django Crispy Forms** - Enhanced form rendering and validation

### Additional Libraries & Tools
- **WeasyPrint 65.1** - PDF generation for reports
- **Pillow 11.2.1** - Image processing and handling
- **Python-decouple 3.8** - Environment variable management
- **Gunicorn 23.0.0** - WSGI HTTP server for deployment

### Development & Deployment
- **ASGI/WSGI** - Asynchronous and synchronous server interfaces
- **Static file management** - CSS, JavaScript, and image serving
- **Template inheritance** - Modular and maintainable UI components

## 🏗️ System Architecture

### Model Architecture
The system uses Django's ORM with the following key models:

1. **Custom User Model** - Extended Django's AbstractUser
   - Role-based differentiation (Admin, HOD, Faculty, Student)
   - Proxy models for specific user types

2. **Academic Structure**
   - Department → Class → Subject hierarchy
   - Faculty assignment to subjects
   - Time-slot based scheduling

3. **Attendance System**
   - Date and time-slot specific attendance marking
   - Bulk attendance operations
   - Automated percentage calculations

4. **Additional Features**
   - Leave request management
   - Announcement system
   - Timetable management

### View Architecture
- **Class-based views** for CRUD operations
- **Function-based views** for specific business logic
- **Custom decorators** for role-based access control
- **Mixin classes** for code reusability

### Template Architecture
- **Base templates** with block inheritance
- **Partial templates** for reusable components
- **Role-specific template directories**
- **Responsive design** with Bootstrap components

## 🎯 Key Features

### Core Functionality
- **Role-based Access Control** - Admin, HOD, Faculty, and Student dashboards
- **Bulk Attendance Marking** - Efficient class-wise attendance recording
- **Automated Report Generation** - PDF/CSV export capabilities
- **Leave Management System** - Request submission and approval workflow
- **Real-time Statistics** - Dashboard analytics and charts

### Advanced Features
- **Intelligent Chatbot** - Natural language queries for system data
- **Consolidated Reporting** - Multi-subject attendance summaries
- **Time-slot Management** - Period-wise attendance tracking
- **Responsive Design** - Mobile and desktop compatibility
- **Data Export** - Multiple format support (PDF, CSV)

### Security Features
- **Custom authentication backend** - Secure login system
- **Role-based permissions** - Access control at view level
- **CSRF protection** - Built-in Django security
- **SQL injection prevention** - ORM-based database queries

## 🔧 How It Works

### Authentication Flow
1. **Custom User Model** extends Django's AbstractUser with role field
2. **Proxy Models** (Student, Faculty, HOD) filter users by role
3. **Custom Managers** provide role-specific querysets
4. **Decorators** enforce access control at view level

### Attendance Management Process
1. **Faculty Login** → Access subject-specific classes
2. **Student Selection** → Bulk or individual marking interface
3. **Time-slot Selection** → Period-specific attendance recording
4. **Database Storage** → Unique constraints prevent duplicates
5. **Report Generation** → Automated percentage calculations

### Report Generation System
1. **Data Aggregation** → Subject-wise attendance collection
2. **Percentage Calculation** → Present/Total attendance ratios
3. **Template Rendering** → HTML report generation
4. **PDF Export** → WeasyPrint conversion for downloads
5. **Statistical Summary** → Class performance metrics

### Chatbot Intelligence
1. **Natural Language Processing** → Regex pattern matching
2. **Database Queries** → Dynamic data retrieval
3. **Response Generation** → Contextual information delivery
4. **Statistical Analysis** → Attendance trends and insights

## 📊 Database Schema

### User Management
```
User (Custom AbstractUser)
├── Student (Proxy) → StudentProfile
├── Faculty (Proxy)
├── HOD (Proxy)
└── Admin
```

### Academic Structure
```
Department
└── Class
    └── Subject
        ├── Faculty (Assignment)
        └── Timetable (Schedule)
```

### Attendance System
```
Attendance
├── Student (Foreign Key)
├── Subject (Foreign Key)
├── Date + TimeSlot (Unique Together)
└── Presence Status (Boolean)
```

## 🚀 Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd college_project
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database:**
   - Install and run PostgreSQL
   - Create a database and user for the project

5. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in database credentials and SECRET_KEY

6. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser (Admin):**
   ```bash
   python manage.py createsuperuser
   ```
   *Set the user's role to 'ADMIN' in the admin panel*

8. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   Access the application at `http://127.0.0.1:8000`

## 👥 User Roles & Permissions

- **Admin**: Complete system management and oversight
- **HOD**: Department-level management and reporting
- **Faculty**: Subject-specific attendance and student management
- **Student**: Personal attendance viewing and leave requests

## 📈 System Benefits

- **Efficiency**: Automated attendance tracking reduces manual effort
- **Accuracy**: Digital records eliminate human errors
- **Accessibility**: Web-based system accessible from anywhere
- **Reporting**: Comprehensive analytics and export capabilities
- **Scalability**: Django framework supports institutional growth