# Render Deployment Guide for Clinic Management System

## Prerequisites
- GitHub repository (push your code there)
- Render account (https://render.com)
- Git installed and repository initialized

## Quick Setup Steps

### 1. Initialize Git (if not already done)
```bash
cd /mnt/newvolume/project/sem3/clinicms
git init
git add .
git commit -m "Initial commit: clinic management system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Create a New Web Service on Render
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Choose the repository and branch (main)

### 3. Configure the Web Service
- **Name:** clinicms (or your preferred name)
- **Runtime:** Python 3
- **Build Command:** Leave default (Render will use render.yaml or Procfile)
- **Start Command:** `gunicorn clinicms.wsgi:application --bind 0.0.0.0:$PORT`
- **Plan:** Free tier (or Pro for production)

### 4. Set Environment Variables
In Render dashboard, go to your service → Environment:

```
DEBUG=False
SECRET_KEY=<generate-a-strong-secret-key>
ALLOWED_HOSTS=yourdomain.onrender.com,www.yourdomain.onrender.com
```

**To generate a SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Configure Database (SQLite limitations)
**Important:** SQLite on Render is not persistent across deployments. 
**Recommended:** Use PostgreSQL (included in Render's free tier for databases).

To use PostgreSQL:
1. In Render, create a PostgreSQL database
2. Get the DATABASE_URL from the database details
3. Add it as an environment variable in your web service
4. Update `settings.py` to use the DATABASE_URL:

```python
import dj_database_url

if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.config(conn_max_age=600)
```

5. Add `dj-database-url` to requirements.txt

### 6. Collect Static Files
Static files are automatically collected during build via the Procfile/render.yaml.
WhiteNoise middleware (added to settings) serves them efficiently.

### 7. Deploy
Push changes to GitHub:
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

Render will automatically:
- Pull your latest code
- Run the build command
- Collect static files
- Run migrations
- Start the server

### 8. Access Your App
Your app will be available at: `https://clinicms.onrender.com` (or your chosen service name)

## Environment Variables Reference

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `DEBUG` | Yes | False | Must be False in production |
| `SECRET_KEY` | Yes | None | Generate a new strong key |
| `ALLOWED_HOSTS` | Yes | localhost | Your Render domain |
| `DATABASE_URL` | No | SQLite | For persistent PostgreSQL |
| `EMAIL_BACKEND` | No | Console | For production emails |
| `EMAIL_HOST` | No | - | SMTP server |

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure all dependencies are in requirements.txt
- Verify Python version compatibility (3.12)

### Static Files Not Loading
- WhiteNoise should handle this automatically
- Check `STATIC_ROOT` and `STATIC_URL` in settings.py
- Verify collectstatic runs during build

### Database Issues
- SQLite data is lost on each deploy
- Use PostgreSQL for persistent data
- Run migrations manually if needed:
  ```
  render deployment logs
  ```

### Domain/SSL Issues
- Render provides free SSL certificates
- Update ALLOWED_HOSTS with your actual domain
- Set SECURE_SSL_REDIRECT=True

## Production Checklist
- [ ] SECRET_KEY is set and strong
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS includes your domain
- [ ] Database is PostgreSQL (not SQLite)
- [ ] Email backend is configured
- [ ] Static files are being served
- [ ] Migrations run successfully
- [ ] Create a superuser for admin access
- [ ] Test login and core features
- [ ] Set up monitoring/alerts on Render

## Create Superuser on Production
```bash
# Via Render shell (in dashboard)
python manage.py createsuperuser
```

Or through the web interface after deploying.

## Rolling Back
To rollback to a previous deployment:
1. In Render dashboard, go to Deployments
2. Click the three dots on a previous deployment
3. Select "Redeploy"

## Additional Resources
- [Render Django Deployment Docs](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)
