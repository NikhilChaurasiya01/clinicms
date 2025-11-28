from django.contrib import admin

# Register your models here

# appointments/admin.py
from django.contrib import admin
from .models import Appointment

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_datetime', 'appointment_type', 'status', 'created_at')
    list_filter = ('status', 'appointment_type', 'appointment_datetime', 'created_at')
    search_fields = ('patient__username', 'doctor__username', 'symptoms', 'notes')
    date_hierarchy = 'appointment_datetime'
    ordering = ('-appointment_datetime',)
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('patient', 'doctor', 'appointment_datetime', 'appointment_type')
        }),
        ('Medical Information', {
            'fields': ('symptoms', 'notes', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at')

