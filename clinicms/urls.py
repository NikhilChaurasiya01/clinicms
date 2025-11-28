"""
URL configuration for clinicms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib import admin
from django.urls import path
from users import views as user_views
from appointments import views as appointment_views
from prescriptions import views as prescription_views

# Import the password reset views
from users.views import (
    CustomPasswordResetView,
    CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetCompleteView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Login
    path("login/", user_views.login_view, name="login"),
    path("logout/", user_views.logout_view, name="logout"),
    path("register/", user_views.register_patient, name="register_patient"),    

    # portal
    path("portal/<str:role>/", user_views.portal_page, name="portal"),
    
    # Role-specific dashboards
    path("dashboard/doctor/", user_views.dashboard_doctor, name="dashboard_doctor"),
    path("dashboard/patient/", user_views.dashboard_patient, name="dashboard_patient"),
    path("dashboard/admin/", user_views.dashboard_admin, name="dashboard_admin"),

    # Prescriptions
    path("prescriptions/add/<int:appointment_id>/", prescription_views.add_prescription, name="add_prescription"),
    path("appointments/<int:appointment_id>/completed/", user_views.mark_completed, name="mark_completed"),

    # Public dashboard (home)
    path('', user_views.public_dashboard, name='public_dashboard'),
    path('portal/<str:role>/', user_views.portal_access, name='portal_access'),

    # Include apps
    path("prescriptions/", include("prescriptions.urls")),
    path("appointments/", include("appointments.urls")),
    
    # Doctor-specific views
    path("doctor/schedule/", user_views.doctor_schedule, name="doctor_schedule"),
    path("doctor/patients/", user_views.doctor_patients_list, name="doctor_patients_list"),
    path("doctor/patients/search/", user_views.doctor_patients_search, name="doctor_patients_search"),
    path("doctor/medical-history/", user_views.doctor_medical_history, name="doctor_medical_history"),
    path("doctor/analytics/", user_views.doctor_analytics, name="doctor_analytics"),
    path("doctor/profile/", user_views.doctor_profile, name="doctor_profile"),

    # Patient-specific URLs
    path("patient/profile/", user_views.patient_profile, name="patient_profile"),
    path("patient/medical-history/", user_views.patient_medical_history, name="patient_medical_history"),
    path('patient/prescriptions/', user_views.patient_prescriptions, name='patient_prescriptions'),
    path('prescription/download/<int:prescription_id>/', user_views.download_prescription, name='download_prescription'),
    path("patient/notifications/", user_views.patient_notifications, name="patient_notifications"),

    # Password Reset URLs
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),



    # Admin Analytics URLs
    path("dashboard/admin/analytics/", user_views.admin_analytics, name="admin_analytics"),
    path("dashboard/admin/reports/", user_views.admin_reports, name="admin_reports"),
    path("dashboard/admin/user-analytics/", user_views.admin_user_analytics, name="admin_user_analytics"),
    path("dashboard/admin/system-health/", user_views.admin_system_health, name="admin_system_health"),
    path("dashboard/admin/export-data/", user_views.admin_export_data, name="admin_export_data"),

    # NEW: Admin Management URLs
    path("dashboard/admin/users/", user_views.admin_users_list, name="admin_users_list"),
    path("dashboard/admin/appointments/", user_views.admin_appointments_list, name="admin_appointments_list"),
    path("dashboard/admin/prescriptions/", user_views.admin_prescriptions_list, name="admin_prescriptions_list"),
]