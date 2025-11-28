from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Dashboard views
    path("dashboard/patient/", views.dashboard_patient, name="dashboard_patient"),
    path("dashboard/doctor/", views.doctor_dashboard, name="dashboard_doctor"),
    
    # Appointment booking and management
    path("book/", views.book_appointment, name="book_appointment"),
    path("list/", views.list_appointments, name="list_appointments"),
    path("upcoming/", views.upcoming_appointments, name="upcoming_appointments"),
    path("history/", views.appointment_history, name="appointment_history"),
    
    # Appointment actions
    path("reschedule/<int:appointment_id>/", views.reschedule_appointment, name="reschedule_appointment"),
    path("cancel/<int:appointment_id>/", views.cancel_appointment, name="cancel_appointment"),
    path("detail/<int:appointment_id>/", views.appointment_detail, name="appointment_detail"),
    
    # Doctor-specific views
    path("complete/<int:appointment_id>/", views.mark_appointment_completed, name="complete_appointment"),
    path("add-notes/<int:appointment_id>/", views.add_appointment_notes, name="add_notes"),
    path("doctor/<int:doctor_id>/availability/", views.doctor_availability, name="doctor_availability"),

     # Patient record view (doctor only)
    path("patient/<int:patient_id>/record/", views.patient_record, name="patient_record"),
]