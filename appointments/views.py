from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.db.models import Q, Count
from datetime import datetime, timedelta
from .models import Appointment, Slot
from users.models import User
from django.http import HttpResponseNotAllowed

# Import your existing Prescription model
try:
    from prescriptions.models import Prescription
except ImportError:
    # If prescriptions app doesn't exist, create a dummy class
    class Prescription:
        objects = type('MockManager', (), {'filter': lambda *args, **kwargs: []})()

@login_required
def dashboard_patient(request):
    """Enhanced patient dashboard with proper statistics"""
    if request.user.role != "patient":
        messages.error(request, "Access denied. Patients only.")
        return redirect("home")
    
    now = timezone.now()
    
    # Get appointments for the patient
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related('doctor').order_by('-appointment_datetime')[:5]  # Show latest 5
    
    # Calculate statistics
    all_appointments = Appointment.objects.filter(patient=request.user)
    
    upcoming_appointments_count = all_appointments.filter(
        appointment_datetime__gte=now,
        status='pending'
    ).count()
    
    pending_appointments_count = all_appointments.filter(
        status='pending'
    ).count()
    
    total_visits = all_appointments.filter(
        status='completed'
    ).count()
    
    # Get prescriptions from your existing prescriptions app
    try:
        prescriptions = Prescription.objects.filter(
            patient=request.user
        ).select_related('doctor').order_by('-date_issued')[:5]
        
        # Count active prescriptions (adjust field name if different in your model)
        active_prescriptions_count = Prescription.objects.filter(
            patient=request.user,
            is_active=True  # Adjust this field name based on your model
        ).count()
    except:
        prescriptions = []
        active_prescriptions_count = 0
    
    context = {
        'appointments': appointments,
        'prescriptions': prescriptions,
        'upcoming_appointments_count': upcoming_appointments_count,
        'pending_appointments_count': pending_appointments_count,
        'active_prescriptions_count': active_prescriptions_count,
        'total_visits': total_visits,
        'now': now,
    }
    
    return render(request, "dashboard/patient.html", context)


@login_required
def book_appointment(request):
    """Book appointment with enhanced validation"""
    if request.user.role != "patient":
        messages.error(request, "Only patients can book appointments.")
        return redirect("home")

    if request.method == "POST":
        doctor_id = request.POST.get("doctor")
        date = request.POST.get("date")
        time = request.POST.get("time")
        appointment_type = request.POST.get("appointment_type", "consultation")
        symptoms = request.POST.get("symptoms", "")
        phone = request.POST.get("phone", "")
        email = request.POST.get("email", "")

        try:
            doctor = User.objects.get(id=doctor_id, role="doctor")

            # Parse date and time
            date_obj = parse_date(date)
            time_obj = parse_time(time)
            if not date_obj or not time_obj:
                messages.error(request, "Invalid date or time format.")
                return redirect("book_appointment")

            datetime_obj = timezone.make_aware(datetime.combine(date_obj, time_obj))
            
            # Validate appointment is in the future
            if datetime_obj <= timezone.now():
                messages.error(request, "Cannot book appointments in the past.")
                return redirect("book_appointment")
            
            # Check for conflicts
            if Appointment.objects.filter(
                doctor=doctor,
                appointment_datetime=datetime_obj,
                status__in=["pending", "completed"]
            ).exists():
                messages.error(request, "This doctor is already booked at the selected time.")
            else:
                appointment = Appointment.objects.create(
                    patient=request.user,
                    doctor=doctor,
                    appointment_datetime=datetime_obj,
                    appointment_type=appointment_type,
                    symptoms=symptoms,
                    phone=phone,
                    email=email
                )
                messages.success(request, f"Appointment booked successfully for {datetime_obj.strftime('%B %d, %Y at %I:%M %p')}!")
                return redirect("dashboard_patient")
                
        except User.DoesNotExist:
            messages.error(request, "Invalid doctor selected.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, "An error occurred while booking the appointment.")

    # Get available doctors
    doctors = User.objects.filter(role="doctor").order_by('username')
    return render(request, "appointments/book.html", {"doctors": doctors})


@login_required
def list_appointments(request):
    """Show appointments based on user role with filtering"""
    if request.user.role == "patient":
        appointments = Appointment.objects.filter(
            patient=request.user
        ).select_related('doctor').order_by("-appointment_datetime")
    elif request.user.role == "doctor":
        appointments = Appointment.objects.filter(
            doctor=request.user
        ).select_related('patient').order_by("-appointment_datetime")
    else:
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'completed', 'cancelled']:
        appointments = appointments.filter(status=status_filter)

    return render(request, "appointments/list.html", {
        "appointments": appointments,
        "status_filter": status_filter
    })


@login_required
def reschedule_appointment(request, appointment_id):
    """Reschedule appointment with enhanced validation"""
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        patient=request.user,
        status='pending'  # Only pending appointments can be rescheduled
    )

    if request.method == "POST":
        new_date_str = request.POST.get("date")
        new_time_str = request.POST.get("time")

        new_date = parse_date(new_date_str)
        new_time = parse_time(new_time_str)
        
        if not new_date or not new_time:
            messages.error(request, "Invalid date or time.")
            return redirect("reschedule_appointment", appointment_id=appointment.id)

        new_datetime = timezone.make_aware(datetime.combine(new_date, new_time))
        
        # Validate new appointment time is in the future
        if new_datetime <= timezone.now():
            messages.error(request, "Cannot reschedule to a past date/time.")
            return redirect("reschedule_appointment", appointment_id=appointment.id)

        # Check if doctor is already booked at that time
        if Appointment.objects.filter(
            doctor=appointment.doctor, 
            appointment_datetime=new_datetime, 
            status__in=["pending", "completed"]
        ).exclude(id=appointment.id).exists():
            messages.error(request, "Doctor is already booked at this time.")
        else:
            old_datetime = appointment.appointment_datetime
            appointment.appointment_datetime = new_datetime
            appointment.is_rescheduled = True
            appointment.save()
            
            messages.success(
                request, 
                f"Appointment rescheduled from {old_datetime.strftime('%B %d, %Y at %I:%M %p')} "
                f"to {new_datetime.strftime('%B %d, %Y at %I:%M %p')}!"
            )
            return redirect("dashboard_patient")

    return render(request, "appointments/reschedule.html", {
        "appointment": appointment
    })


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        patient=request.user,
        status='pending'  # Only allow cancelling pending ones
    )

    if request.method == "POST":
        appointment.status = "cancelled"
        appointment.save()

        messages.success(
            request, 
            f"Appointment with Dr. {appointment.doctor.username} on "
            f"{appointment.appointment_datetime.strftime('%B %d, %Y at %I:%M %p')} "
            "has been cancelled successfully!"
        )
        return redirect("dashboard_patient")

    return HttpResponseNotAllowed(["POST"])


@login_required
def appointment_detail(request, appointment_id):
    """View detailed information about an appointment"""
    if request.user.role == "patient":
        appointment = get_object_or_404(
            Appointment, 
            id=appointment_id, 
            patient=request.user
        )
    elif request.user.role == "doctor":
        appointment = get_object_or_404(
            Appointment, 
            id=appointment_id, 
            doctor=request.user
        )
    else:
        messages.error(request, "Unauthorized access.")
        return redirect("home")

    return render(request, "appointments/detail.html", {
        "appointment": appointment
    })


@login_required  
def doctor_availability(request, doctor_id):
    """Get available time slots for a specific doctor"""
    doctor = get_object_or_404(User, id=doctor_id, role="doctor")
    
    # Get date from request (default to today)
    date_str = request.GET.get('date', timezone.now().date().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()
    
    # Don't show availability for past dates
    if selected_date < timezone.now().date():
        available_slots = []
    else:
        # Get booked appointments for this doctor on this date
        booked_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_datetime__date=selected_date,
            status__in=['pending', 'completed']
        ).values_list('appointment_datetime__time', flat=True)
        
        # Generate time slots (9 AM to 5 PM, 30-minute intervals)
        available_slots = []
        start_time = datetime.strptime('09:00', '%H:%M').time()
        end_time = datetime.strptime('17:00', '%H:%M').time()
        current_time = datetime.combine(selected_date, start_time)
        end_datetime = datetime.combine(selected_date, end_time)
        
        while current_time < end_datetime:
            if current_time.time() not in booked_appointments:
                # Skip past times for today
                if selected_date == timezone.now().date():
                    if timezone.make_aware(current_time) > timezone.now():
                        available_slots.append(current_time.time())
                else:
                    available_slots.append(current_time.time())
            current_time += timedelta(minutes=30)
    
    return render(request, "appointments/availability.html", {
        "doctor": doctor,
        "selected_date": selected_date,
        "available_slots": available_slots
    })


# Additional utility views for better user experience

@login_required
def upcoming_appointments(request):
    """Show only upcoming appointments for patients"""
    if request.user.role != "patient":
        messages.error(request, "Access denied.")
        return redirect("home")
    
    now = timezone.now()
    appointments = Appointment.objects.filter(
        patient=request.user,
        appointment_datetime__gte=now,
        status='pending'
    ).select_related('doctor').order_by('appointment_datetime')
    
    return render(request, "appointments/upcoming.html", {
        "appointments": appointments
    })


@login_required
def appointment_history(request):
    """Show appointment history for patients"""
    if request.user.role != "patient":
        messages.error(request, "Access denied.")
        return redirect("home")
    
    appointments = Appointment.objects.filter(
        patient=request.user,
        status__in=['completed', 'cancelled']
    ).select_related('doctor').order_by('-appointment_datetime')
    
    return render(request, "appointments/history.html", {
        "appointments": appointments
    })


# Doctor-specific views (FIXED VERSION)

@login_required
def doctor_dashboard(request):
    """Dashboard for doctors - FIXED VERSION"""
    if request.user.role != "doctor":
        messages.error(request, "Access denied. Doctors only.")
        return redirect("home")
    
    now = timezone.now()
    today = now.date()
    
    # Get today's appointments
    todays_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_datetime__date=today
    ).select_related('patient').order_by('appointment_datetime')
    
    # Get upcoming appointments (next 7 days)
    upcoming_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_datetime__gte=now,
        appointment_datetime__date__lte=today + timedelta(days=7),
        status='pending'
    ).select_related('patient').order_by('appointment_datetime')
    
    # Calculate statistics
    all_appointments = Appointment.objects.filter(doctor=request.user)
    total_patients = all_appointments.values('patient').distinct().count()
    pending_appointments_count = all_appointments.filter(status='pending').count()
    
    # Get prescriptions - try to get recent prescriptions for the dashboard
    try:
        prescriptions = Prescription.objects.filter(
            doctor=request.user
        ).select_related('patient').order_by('-date_issued')[:5]
        prescriptions_count = Prescription.objects.filter(doctor=request.user).count()
    except:
        prescriptions = []
        prescriptions_count = 0

    context = {
        'todays_appointments_count': todays_appointments.count(),
        'total_patients': total_patients,
        'prescriptions_count': prescriptions_count,
        'pending_appointments': pending_appointments_count,  # Fixed variable name
        'appointments': upcoming_appointments,
        'todays_appointments': todays_appointments,
        'prescriptions': prescriptions,  # Add prescriptions to context
        'today': today,
        'now': now,  # Add current time for template use
    }
    
    return render(request, "users/dashboard_doctor.html", context)


@login_required
def mark_appointment_completed(request, appointment_id):
    """Mark an appointment as completed (doctor only)"""
    if request.user.role != "doctor":
        messages.error(request, "Access denied.")
        return redirect("home")
    
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        doctor=request.user,
        status='pending'
    )
    
    if request.method == "POST":
        notes = request.POST.get('notes', '')
        appointment.status = 'completed'
        appointment.notes = notes
        appointment.save()
        
        messages.success(
            request, 
            f"Appointment with {appointment.patient.username} marked as completed."
        )
        return redirect("appointments:dashboard_doctor")  # Fixed redirect with namespace
    
    return render(request, "appointments/complete.html", {
        "appointment": appointment
    })


@login_required
def add_appointment_notes(request, appointment_id):
    """Add or update notes for an appointment (doctor only)"""
    if request.user.role != "doctor":
        messages.error(request, "Access denied.")
        return redirect("home")
    
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        doctor=request.user
    )
    
    if request.method == "POST":
        notes = request.POST.get('notes', '').strip()
        appointment.notes = notes
        appointment.save()
        
        if notes:
            messages.success(request, "Notes added successfully.")
        else:
            messages.success(request, "Notes updated successfully.")
        
        return redirect("appointments:dashboard_doctor")
    
    return redirect("appointments:dashboard_doctor")


@login_required
def patient_record(request, patient_id):
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect("home")

    patient = get_object_or_404(User, id=patient_id, role='patient')

    past_appointments = Appointment.objects.filter(
        patient=patient
    ).select_related('doctor').order_by('-appointment_datetime')

    prescriptions = Prescription.objects.filter(
        patient=patient
    ).select_related('doctor').order_by('-date_issued')

    has_consulted_before = past_appointments.exists()

    context = {
        'patient': patient,
        'appointments': past_appointments,
        'prescriptions': prescriptions,
        'has_consulted_before': has_consulted_before,
    }

    return render(request, 'patients/record.html', context)


