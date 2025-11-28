from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()

class Appointment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    TYPE_CHOICES = [
        ("consultation", "Consultation"),
        ("follow_up", "Follow-up"),
        ("emergency", "Emergency"),
        ("check_up", "Check-up"),
    ]

    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="appointments_as_patient"
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="appointments_as_doctor"
    )
    
    # Main appointment datetime
    appointment_datetime = models.DateTimeField()
    
    # Additional fields
    appointment_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="consultation"
    )
    
    symptoms = models.TextField(
        blank=True, 
        null=True,
        help_text="Patient's symptoms or reason for visit"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Doctor's notes after consultation"
    )
    phone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        help_text="Contact phone number"
    )
    email = models.EmailField(
        blank=True, 
        null=True,
        help_text="Contact email address"
    )

    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="pending"
    )
    
    # Tracking fields
    is_rescheduled = models.BooleanField(
        default=False,
        help_text="True if this appointment has been rescheduled"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment_datetime"]
        # Remove unique constraint to allow rescheduling
        indexes = [
            models.Index(fields=['doctor', 'appointment_datetime']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['appointment_datetime']),
        ]

    def clean(self):
        """Custom validation"""
        super().clean()
        
        # Validate appointment is in the future (except for completed ones)
        if self.appointment_datetime and self.status not in ['completed', 'cancelled']:
            if self.appointment_datetime <= timezone.now():
                raise ValidationError("Appointments must be scheduled for future dates.")

        
        # Check for conflicts only if not cancelled
        if self.status != "cancelled" and self.appointment_datetime:
            conflict = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_datetime=self.appointment_datetime,
                status__in=["pending", "completed"]
            ).exclude(id=self.id if self.id else None)
            
            if conflict.exists():
                raise ValidationError(
                    f"Dr. {self.doctor.username} already has an appointment at this time."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        """Check if appointment is upcoming"""
        return self.appointment_datetime > timezone.now() and self.status == 'pending'
    
    @property
    def is_today(self):
        """Check if appointment is today"""
        return self.appointment_datetime.date() == timezone.now().date()
    
    @property
    def time_until_appointment(self):
        """Get time until appointment"""
        if self.is_upcoming:
            delta = self.appointment_datetime - timezone.now()
            days = delta.days
            hours = delta.seconds // 3600
            
            if days > 0:
                return f"in {days} day{'s' if days != 1 else ''}"
            elif hours > 0:
                return f"in {hours} hour{'s' if hours != 1 else ''}"
            else:
                return "soon"
        return None

    def __str__(self):
        return f"{self.patient.username} → Dr. {self.doctor.username} on {self.appointment_datetime.strftime('%Y-%m-%d %H:%M')} ({self.status})"


class Slot(models.Model):
    """Doctor availability slots"""
    doctor = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="slots"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    
    # Slot types
    SLOT_TYPES = [
        ('regular', 'Regular'),
        ('emergency', 'Emergency'),
        ('blocked', 'Blocked'),  # For doctor's personal time
    ]
    slot_type = models.CharField(
        max_length=20,
        choices=SLOT_TYPES,
        default='regular'
    )

    class Meta:
        ordering = ['start_time']
        unique_together = ('doctor', 'start_time')

    def clean(self):
        """Validate slot times"""
        super().clean()
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time.")
            
            if self.start_time < timezone.now():
                raise ValidationError("Cannot create slots in the past.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration(self):
        """Get slot duration in minutes"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 0

    def __str__(self):
        status = "Available" if self.is_available else "Booked"
        return f"Dr. {self.doctor.username}: {self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')} ({status})"


# Prescription model removed from here since you have a separate prescriptions app
# The dashboard will work with your existing prescriptions.Prescription model