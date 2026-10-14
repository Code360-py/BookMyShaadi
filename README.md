# BookMyShaadi

A two-sided wedding and event planning platform built with Django, featuring a public website, a customer portal, and a staff management backend.

## Features

### Public Website
- Landing page
- Services and packages
- Vendor listings
- Gallery
- Customer enquiries

### Customer Portal
- Customer registration and login
- Personal dashboard
- My events
- My bookings
- Profile management

### Staff Backend
- Enquiry management
- Customer management
- Booking management
- Event management
- Vendor management
- Collaborations
- Task management
- Expense tracking
- Payment management
- Audit logs
- Staff management with role-based access control

## Technology Stack

- **Backend:** Django 5.0+
- **Language:** Python 3.11+
- **Database:** Database configured in Django settings
- **Authentication:** Custom PBKDF2-HMAC-SHA256 password hashing
- **Sessions:** Separate customer and staff sessions
- **Frontend:** HTML, CSS, and JavaScript
- **UI:** iPhone-inspired dark interface

## Requirements

- Python 3.11+
- Django 5.0+
- Git

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Code360-py/BookMyShaadi.git
cd BookMyShaadi
```

### 2. Create and Activate a Virtual Environment

**Linux / macOS**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
python manage.py migrate
```

### 5. Seed Packages and Demo Data

```bash
python manage.py seed_packages
python manage.py seed_public_content
python manage.py seed_demo
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Demo Credentials

| User Type | Login URL | Email | Password |
|---|---|---|---|
| Staff Admin | `/login/?tab=staff` | `admin@bookmyshaadi.local` | `admin12345` |
| Staff | `/login/?tab=staff` | `staffN@bookmyshaadi.local` | `demo12345` |
| Customer | `/login/?tab=customer` | `customerN@example.com` | `demo12345` |

Replace `N` with a number from **1 to 100** for staff accounts or **1 to 120** for customer accounts.

**Security warning:** These credentials are for local demonstration only. Never use them in production.

## Project Structure

```text
BookMyShaadi/
├── BookMyShaadi/    # Django settings and root URLs
├── accounts/        # Customer and staff models and authentication
├── core/            # Public website, services, packages and contact
├── bookings/        # Enquiries and bookings
├── events/          # Events, packages and gallery images
├── vendors/         # Vendors and collaborations
├── finance/         # Expenses and payments
├── tasks/           # Task management
├── staffpanel/      # Staff backend, views, URLs and templates
├── audit/           # Audit logging
├── templates/       # Shared and application templates
├── static/
│   └── css/
│       └── app.css  # Application design system
└── manage.py        # Django management utility
```

## Common Management Commands

### Reset Demo Data

```bash
python manage.py seed_demo --wipe
```

**Warning:** Review the command implementation before using `--wipe`, as it may delete existing demo data.

### Create a Staff Admin

```bash
python manage.py create_admin <email> <name> <password>
```

Replace the placeholders with the desired email, name and password.

### Check the Project

```bash
python manage.py check
```

## Security Features

- PBKDF2-HMAC-SHA256 password hashing with 260,000 iterations and a unique per-user salt.
- Separate sessions for customers and staff.
- Login lockout after repeated failed attempts.
- Role-based staff access using `ADMIN`, `MANAGER` and `STAFF` roles.
- Audit logging for write operations.
- Environment-based application secrets.
- Custom user management without `django.contrib.auth`.

### Production Security Checklist

- Verify CSRF protection and secure session cookies.
- Configure session expiration and login rate limiting.
- Enforce authorization checks for sensitive operations.
- Review password-reset and account-recovery flows.
- Protect audit logs against unauthorized modification.
- Use HTTPS and secure secret management.
- Secure the database and environment variables.

Custom authentication requires a thorough security review before production deployment.

## License

This is a private project. All rights are reserved unless otherwise specified by the project owner.
