# Clinic Management System

A comprehensive Django-based clinic management system for managing patients, doctors, appointments, and prescriptions.

## Features

- **User Management**: Separate portals for doctors, patients, and administrators
- **Appointment Booking**: Schedule and manage appointments with doctors
- **Prescription Management**: Create and manage patient prescriptions
- **Medical History**: Track patient medical records
- **Doctor Schedules**: Manage doctor availability and schedules
- **Analytics Dashboard**: View system analytics and reports

## Tech Stack

- **Backend**: Django 5.2.5
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Authentication**: Django Allauth
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Deployment**: Render

## GitHub Repository

[https://github.com/NikhilChaurasiya01/clinicms](https://github.com/NikhilChaurasiya01/clinicms)

## Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/NikhilChaurasiya01/clinicms.git
   cd clinicms
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Open your browser and go to: `http://127.0.0.1:8000/`

## Deployment on Render

### Prerequisites
- GitHub account with repository access
- Render account ([sign up here](https://render.com))

### Deployment Steps

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository: `NikhilChaurasiya01/clinicms`

3. **Configure the Web Service**
   - **Name**: `clinicms` (or your preferred name)
   - **Region**: Choose the closest region
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
     ```
   - **Start Command**: 
     ```bash
     gunicorn clinicms.wsgi:application
     ```

4. **Set Environment Variables**
   In the Render dashboard, add these environment variables:
   
   - `DEBUG` = `False`
   - `SECRET_KEY` = (generate a secure key using `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `ALLOWED_HOSTS` = `your-app-name.onrender.com` (replace with your actual Render URL)

5. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application
   - Wait for the deployment to complete

6. **Access your deployed application**
   - Your app will be available at: `https://your-app-name.onrender.com`

### Alternative: Using render.yaml (Blueprint)

This project includes a `render.yaml` file for automated deployment:

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and configure your service
5. Set the `ALLOWED_HOSTS` environment variable to your Render URL after deployment

### Post-Deployment

1. **Create a superuser** (for admin access)
   - Go to your Render dashboard
   - Navigate to your service's "Shell" tab
   - Run: `python manage.py createsuperuser`
   - Follow the prompts to create your admin account

2. **Access the admin panel**
   - Visit: `https://your-app-name.onrender.com/admin/`

## Important Notes

- **Database**: By default, the app uses SQLite. For production on Render, consider using PostgreSQL:
  - Add a PostgreSQL database in Render
  - Update `DATABASE_URL` environment variable
  - Modify `settings.py` to use PostgreSQL

- **Static Files**: Handled by WhiteNoise for efficient serving

- **Security**: 
  - Never commit your `.env` file or expose `SECRET_KEY`
  - Always set `DEBUG=False` in production
  - Use strong passwords for all accounts

## Support

For issues or questions, please open an issue on the [GitHub repository](https://github.com/NikhilChaurasiya01/clinicms/issues).

## License

This project is for educational purposes.
