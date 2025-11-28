from django.urls import path
from . import views

app_name = 'prescriptions'

urlpatterns = [
    path("add/<int:appointment_id>/", views.add_prescription, name="add_prescription"),
    path("edit/<int:pk>/", views.edit_prescription, name="edit_prescription"),  # 👈 new
    path('prescriptions/<int:pk>/print/', views.print_prescription, name='print_prescription'),
    # New URLs for sidebar functionality
    path('list/', views.list_prescriptions, name='list_prescriptions'),
    path('active/', views.active_prescriptions, name='active_prescriptions'),
    path('templates/', views.prescription_templates, name='templates'),
]
