from django.contrib import admin

# Register your models here.
# prescriptions/admin.py
from django.contrib import admin
from .models import Prescription

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('get_patient_name', 'doctor', 'medicine', 'dosage', 'date_issued', 'appointment')
    list_filter = ('date_issued', 'doctor')
    search_fields = ('medicine', 'doctor__username', 'appointment__patient__username')
    date_hierarchy = 'date_issued'
    ordering = ('-date_issued',)
    
    fieldsets = (
        ('Prescription Details', {
            'fields': ('doctor', 'appointment', 'medicine', 'dosage')
        }),
        ('Instructions', {
            'fields': ('instructions', 'date_issued')
        })
    )
    
    def get_patient_name(self, obj):
        return obj.appointment.patient.get_full_name() or obj.appointment.patient.username
    get_patient_name.short_description = 'Patient'
    get_patient_name.admin_order_field = 'appointment__patient__username'