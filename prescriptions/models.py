from django.db import models

# Create your models here.
from django.db import models
from users.models import User
from appointments.models import Appointment

class Prescription(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="prescription"
    )
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prescriptions")
    patient = models.ForeignKey(User,on_delete=models.CASCADE,related_name="patient_prescriptions", null=True,blank=True)
    medicine = models.CharField(max_length=200, default="Not specified")
    dosage = models.CharField(max_length=100, blank=True, null=True)
    instructions = models.TextField()
    date_issued = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        try:
            if self.appointment and self.appointment.patient:
                patient_name = self.appointment.patient.username
            else:
                patient_name = "Unknown Patient"
            
            if self.doctor:
                doctor_name = self.doctor.username
            else:
                doctor_name = "Unknown Doctor"
                
            return f"Prescription for {patient_name} by {doctor_name}"
        except:
            return f"Prescription #{self.id}"
