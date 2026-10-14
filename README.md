# BookMyShaadi

A two-sided wedding & event planning platform.

- Public site — landing, services, packages, vendors, gallery, enquiry
- Customer area — register, dashboard, my events, my bookings, profile
- Staff backend — enquiries, customers, bookings, events, vendors, collaborations, tasks, expenses, payments, audit log, staff management

Built with Django, plain models, custom PBKDF2 hashing, session-based auth for two independent user types, and an iPhone-style dark UI.

## Requirements

- Python 3.11+
- Django 5.0+

## Setup
’’’bash
git clone https://github.com/Code360-py/BookMyShaadi.git
cd BookMyShaadi
python -m venv .venv
source .venv/bin/activate
pip install django
python manage.py migrate
python manage.py seed_packages
python manage.py seed_demo
python manage.py runserver
’’’
Open http://127.0.0.1:8000/

## Demo credentials

Staff admin   /login/?tab=staff      admin@bookmyshaadi.local / admin12345
Staff (any)   /login/?tab=staff      staffN@bookmyshaadi.local / demo12345
Customer      /login/?tab=customer   customerN@example.com / demo12345

Where N is 1..100 for staff and 1..120 for customers.
Do not use these credentials in production.

## Layout

BookMyShaadi/          Django project (settings, root urls)
accounts/              Customer + Staff models, auth, unified login
core/                  Public site (home, services, packages, gallery, contact)
bookings/              Enquiry + Booking
events/                Event, Package, GalleryImage
vendors/               Vendor + Collaboration
finance/               Expense + Payment
tasks/                 Task
staffpanel/            Staff backend views, urls, templates
audit/                 Audit log
templates/             Shared + per-app templates
static/css/app.css     Design system

## Common commands

python manage.py seed_demo --wipe
python manage.py create_admin <email> <name> <password>
python manage.py check

## Security

- No django.contrib.auth for user management
- PBKDF2-HMAC-SHA256 password hashing (260k iterations, per-user salt)
- Separate sessions for customers and staff
- Login lockout after failed attempts
- Role-gated staff backend (ADMIN / MANAGER / STAFF)
- Audit log records every write action
- Secrets read from environment, never hardcoded

## License

Private project.
