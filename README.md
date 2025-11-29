# 🏥 Clinic Management System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2.5-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

A comprehensive, modern clinic management system built with Django for managing patients, doctors, appointments, and prescriptions. Features separate portals for different user roles with intuitive dashboards and analytics.

![Clinic Management System](https://img.shields.io/badge/Status-Active-success)

## ✨ Features

### 👥 User Management
- **Multi-Role System**: Separate portals for Doctors, Patients, and Administrators
- **Secure Authentication**: Built with Django Allauth
- **User Profiles**: Detailed profiles for doctors and patients
- **Role-Based Access Control**: Different permissions for each user type

### 📅 Appointment Management
- **Easy Booking**: Patients can book appointments with available doctors
- **Schedule Management**: Doctors can manage their availability and time slots
- **Appointment History**: Track past and upcoming appointments
- **Status Tracking**: Monitor appointment status (pending, confirmed, completed, cancelled)
- **Rescheduling**: Flexible appointment rescheduling system

### 💊 Prescription Management
- **Digital Prescriptions**: Create and manage prescriptions electronically
- **Medication Tracking**: Complete medication details with dosage instructions
- **Prescription History**: Access complete prescription records
- **Print Functionality**: Print prescriptions for patients

### 📊 Analytics & Reports
- **Admin Dashboard**: Comprehensive analytics for system administrators
- **Doctor Analytics**: Performance metrics and appointment statistics
- **Patient Statistics**: Track patient visits and medical history
- **System Health Monitoring**: Monitor system performance and usage

### 🔐 Security Features
- **Secure Authentication**: Password hashing and secure session management
- **CSRF Protection**: Built-in Django CSRF protection
- **SSL/TLS Support**: HTTPS ready for production
- **Session Management**: Auto-logout and session timeout features

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Django 5.2.5** | Backend Framework |
| **Python 3.12** | Programming Language |
| **SQLite / PostgreSQL** | Database |
| **Django Allauth** | Authentication |
| **WhiteNoise** | Static File Serving |
| **Gunicorn** | WSGI HTTP Server |
| **Bootstrap 5** | Frontend Framework |
| **JavaScript** | Frontend Interactivity |
| **Render** | Cloud Deployment |

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- pip (Python package manager)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/NikhilChaurasiya01/clinicms.git
   cd clinicms
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Main Application: `http://127.0.0.1:8000/`
   - Admin Panel: `http://127.0.0.1:8000/admin/`
   - Doctor Portal: `http://127.0.0.1:8000/portal/doctor/`
   - Patient Portal: `http://127.0.0.1:8000/portal/patient/`

## 📦 Project Structure

```
clinicms/
├── appointments/          # Appointment management app
├── prescriptions/         # Prescription management app
├── users/                 # User management and authentication
├── clinicms/             # Main project settings
├── staticfiles/          # Collected static files
├── templates/            # HTML templates
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
├── render.yaml          # Render deployment config
└── README.md            # This file
```

## 🌐 Deployment on Render

### Method 1: Using Blueprint (Recommended)

This project includes a `render.yaml` file for automated deployment:

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository: `NikhilChaurasiya01/clinicms`
4. Render will automatically detect `render.yaml` and configure your service
5. Click **"Apply"** to deploy

### Method 2: Manual Deployment

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
   - **Start Command**: `gunicorn clinicms.wsgi:application`
5. Add environment variables:
   - `DEBUG` = `False`
   - `SECRET_KEY` = (generate using: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `ALLOWED_HOSTS` = `.onrender.com`

### Post-Deployment Steps

1. **Create Superuser Account**
   - Go to Render Dashboard → Your Service → **Shell** tab
   - Run:
     ```bash
     python manage.py createsuperuser
     ```

2. **Access Your Application**
   - Main App: `https://your-app-name.onrender.com/`
   - Admin Panel: `https://your-app-name.onrender.com/admin/`

## 📝 Usage Guide

### For Patients
1. Register or log in to the patient portal
2. Browse available doctors and specializations
3. Book appointments with preferred doctors
4. View appointment history and upcoming appointments
5. Access medical records and prescriptions

### For Doctors
1. Log in to the doctor portal
2. Manage availability and time slots
3. View and manage patient appointments
4. Create and manage prescriptions
5. Access patient medical history
6. View analytics and performance metrics

### For Administrators
1. Access the admin panel
2. Manage users (doctors, patients)
3. Monitor system analytics
4. View system health and performance
5. Generate reports

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Django secret key | Auto-generated |
| `ALLOWED_HOSTS` | Allowed host domains | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection URL | SQLite (default) |

## 🐛 Troubleshooting

### Common Issues

**Issue**: `DisallowedHost` error
- **Solution**: Add your domain to `ALLOWED_HOSTS` environment variable

**Issue**: Static files not loading
- **Solution**: Run `python manage.py collectstatic` and ensure WhiteNoise is configured

**Issue**: Database errors on Render
- **Solution**: Ensure migrations run in build command

**Issue**: Service sleeping on free tier
- **Solution**: First request after 15 minutes of inactivity takes ~30-60 seconds

## 📊 Features in Detail

### Appointment System
- Real-time availability checking
- Time slot management
- Email notifications (optional)
- Appointment rescheduling
- Cancellation handling

### Prescription Management
- Comprehensive medication details
- Dosage instructions
- Digital prescription generation
- Print-ready format
- Prescription history tracking

### Analytics Dashboard
- Patient statistics
- Appointment trends
- Doctor performance metrics
- System usage analytics

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is created for educational purposes.

## 👨‍💻 Author

**Nikhil Chaurasiya**
- GitHub: [@NikhilChaurasiya01](https://github.com/NikhilChaurasiya01)

## 🙏 Acknowledgments

- Django documentation and community
- Bootstrap for UI components
- Render for hosting platform

---

<div align="center">
  <p>Made with ❤️ using Django</p>
  <p>⭐ Star this repo if you find it useful!</p>
</div>

