from django.shortcuts import render

# Create your views here.
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from appointments.models import Appointment
from prescriptions.models import Prescription
from .forms import PrescriptionForm
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Max, Sum
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
import json
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.urls import reverse_lazy
from .forms import CustomPasswordResetForm, CustomSetPasswordForm
User = get_user_model()


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Re-authenticate before login
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=raw_password)
            if user is not None:
                login(request, user)

            # redirect based on role
            if user.role == "doctor":
                return redirect("dashboard_doctor")
            elif user.role == "patient":
                return redirect("dashboard_patient")
            else:  # admin
                return redirect("dashboard_admin")
    else:
        form = RegisterForm()
    return render(request, "users/register_patient.html", {"form": form})


def login_view(request):
    role = request.GET.get("role", "")  # keep using GET
    
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user:
            # Check role matches
            if role and getattr(user, "role", "") != role:
                messages.error(request, f"You are not allowed to log in as {role}.")
                return render(request, "users/login.html", {"role": role})

            login(request, user)

            # Redirect to the correct dashboard
            if user.role == "doctor":
                return redirect("dashboard_doctor")  # or "dashboard_doctor" if you split later
            elif user.role == "patient":
                return redirect("dashboard_patient")
            else:  # admin
                return redirect("dashboard_admin")
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, "users/login.html", {"role": role})


@login_required
def dashboard_doctor(request):
    appointments = Appointment.objects.filter(doctor=request.user)
    prescriptions = Prescription.objects.filter(doctor=request.user)
    return render(
        request,
        "users/dashboard_doctor.html",
        {"appointments": appointments, "prescriptions": prescriptions},
    )

@login_required
def dashboard_patient(request):
    """Patient dashboard with stats, appointments, prescriptions, and next appointment"""
    if request.user.role != "patient":
        messages.error(request, "Access denied.")
        return redirect("login")

    now = timezone.now()

    # Get all appointments & prescriptions for this patient
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related("doctor").order_by("-appointment_datetime")

    prescriptions = Prescription.objects.filter(
        appointment__patient=request.user
    ).select_related("doctor", "appointment").order_by("-date_issued")

    # Stats
    upcoming_appointments_count = appointments.filter(
        appointment_datetime__gte=now
    ).count()

    pending_appointments_count = appointments.filter(status="pending").count()
    completed_appointments_count = appointments.filter(status="completed").count()
    active_prescriptions_count = prescriptions.count()

    # Recent activities
    recent_appointments = appointments[:5]
    recent_prescriptions = prescriptions[:5]

    # Next appointment (closest upcoming)
    next_appointment = appointments.filter(
        appointment_datetime__gte=now
    ).order_by("appointment_datetime").first()

    context = {
        "appointments": recent_appointments,
        "prescriptions": recent_prescriptions,
        "upcoming_appointments_count": upcoming_appointments_count,
        "pending_appointments_count": pending_appointments_count,
        "completed_appointments_count": completed_appointments_count,
        "active_prescriptions_count": active_prescriptions_count,
        "total_visits": completed_appointments_count,
        "next_appointment": next_appointment,
    }

    return render(request, "users/dashboard_patient.html", context)



# Replace your existing dashboard_admin view with this enhanced version

@login_required
def dashboard_admin(request):
    """Enhanced admin dashboard with analytics preview"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # Basic stats for the dashboard
    total_users = User.objects.count()
    total_doctors = User.objects.filter(role='doctor').count()
    total_patients = User.objects.filter(role='patient').count()
    total_admins = User.objects.filter(role='admin').count()
    
    # Growth metrics
    new_users_this_month = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).count()
    
    new_patients_this_month = User.objects.filter(
        role='patient',
        date_joined__gte=thirty_days_ago
    ).count()
    
    new_doctors_this_month = User.objects.filter(
        role='doctor',
        date_joined__gte=thirty_days_ago
    ).count()
    
    # Appointment stats
    total_appointments = Appointment.objects.count()
    today_appointments = Appointment.objects.filter(
        appointment_datetime__date=now.date()
    ).count()
    
    completed_appointments = Appointment.objects.filter(
        status='completed'
    ).count()
    
    pending_appointments = Appointment.objects.filter(
        status='pending'
    ).count()
    
    # Calculate completion rate
    appointment_completion_rate = round(
        (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0,
        1
    )
    
    # Active patients (had appointment in last 30 days)
    active_patients = User.objects.filter(
        role='patient',
        appointments_as_patient__appointment_datetime__gte=thirty_days_ago
    ).distinct().count()
    
    # Prescription stats
    try:
        total_prescriptions = Prescription.objects.count()
        monthly_prescriptions = Prescription.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
    except:
        total_prescriptions = 0
        monthly_prescriptions = 0
    
    # Total records in system
    total_records = total_users + total_appointments + total_prescriptions
    
    context = {
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_admins': total_admins,
        'new_users_this_month': new_users_this_month,
        'new_patients_this_month': new_patients_this_month,
        'new_doctors_this_month': new_doctors_this_month,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
        'appointment_completion_rate': appointment_completion_rate,
        'active_patients': active_patients,
        'total_prescriptions': total_prescriptions,
        'monthly_prescriptions': monthly_prescriptions,
        'total_records': total_records,
    }
    
    return render(request, "users/dashboard_admin.html", context)

    


def public_dashboard(request):
    " This is the landing page where users can see general information "
    return render(request, "users/public_dashboard.html")

def logout_view(request):
    logout(request)
    return redirect("public_dashboard")


def portal_page(request, role):
    """Portal landing page for each role"""
    return render(request, "users/portal_page.html", {"role": role})
def register_patient(request):
    """Register a new patient"""
    doctors = User.objects.filter(role="doctor")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "patient"  # Set role to patient
            user.save()

            # Re-authenticate before login
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=user.username, password=raw_password)
            if user is not None:
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")                
                return redirect("dashboard_patient")
    else:
        form = RegisterForm()
    return render(request, "users/register_patient.html", {"form": form, "doctors": doctors})

def add_prescription(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.appointment = appointment
            prescription.doctor = request.user  # logged-in doctor
            prescription.patient = appointment.patient  # link to patient
            prescription.save()

            return redirect("dashboard_doctor")  # ✅ send doctor back
    else:
        form = PrescriptionForm()

    return render(request, "prescriptions/add_prescription.html", {"form": form, "appointment": appointment})






def mark_completed(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user)

    if request.method == "POST":
        appointment.status = "completed"
        appointment.save()
        messages.success(request, "Appointment marked as consulted.")
        return redirect("dashboard_doctor")

    return redirect("dashboard_doctor")

@login_required
def doctor_schedule(request):
    """Display doctor's weekly schedule"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    # Get current week's appointments
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_datetime__date__range=[week_start, week_end]
    ).select_related('patient').order_by('appointment_datetime')
    
    # Group appointments by day
    schedule_by_day = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        schedule_by_day[day] = appointments.filter(appointment_datetime__date=day)
    
    context = {
        'schedule_by_day': schedule_by_day,
        'week_start': week_start,
        'week_end': week_end,
        'today': today
    }
    
    return render(request, 'users/doctor_schedule.html', context)

@login_required
def doctor_patients_list(request):
    """List all patients who have had appointments with this doctor"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    # Get all patients who have had appointments with this doctor
    patient_ids = Appointment.objects.filter(
        doctor=request.user
    ).values_list('patient_id', flat=True).distinct()
    
    patients = User.objects.filter(
        id__in=patient_ids,
        role='patient'
    ).annotate(
    total_appointments=Count(
        'appointments_as_patient',
        filter=Q(appointments_as_patient__doctor=request.user)
    ),
    last_visit=Max(
        'appointments_as_patient__appointment_datetime',
        filter=Q(appointments_as_patient__doctor=request.user)
    )
).order_by('username')
    
    # Pagination
    paginator = Paginator(patients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'patients': page_obj,
        'total_patients': patients.count()
    }
    
    return render(request, 'users/patient_list.html', context)

@login_required
def doctor_patients_search(request):
    """Search for patients"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    query = request.GET.get('q', '')
    results = []
    
    if query:
        # Get all patients who have had appointments with this doctor
        patient_ids = Appointment.objects.filter(
            doctor=request.user
        ).values_list('patient_id', flat=True).distinct()
        
        results = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(email__icontains=query),
            id__in=patient_ids,
            role='patient'
        ).annotate(
    total_appointments=Count(
        'appointments_as_patient',
        filter=Q(appointments_as_patient__doctor=request.user)
    ),
    last_visit=Max(
        'appointments_as_patient__appointment_datetime',
        filter=Q(appointments_as_patient__doctor=request.user)
    )
)[:20]
    
    context = {
        'query': query,
        'results': results,
        'results_count': len(results) if results else 0
    }
    
    return render(request, 'users/patient_search.html', context)

@login_required
def doctor_medical_history(request):
    """View comprehensive medical history of patients"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    # Get recent completed appointments with notes
    recent_consultations = Appointment.objects.filter(
        doctor=request.user,
        status='completed'
    ).exclude(
        notes__isnull=True
    ).exclude(
        notes=''
    ).select_related('patient').order_by('-appointment_datetime')[:50]
    
    # Get statistics
    total_consultations = Appointment.objects.filter(
        doctor=request.user,
        status='completed'
    ).count()
    
    context = {
        'recent_consultations': recent_consultations,
        'total_consultations': total_consultations
    }
    
    return render(request, 'users/medical_history.html', context)

@login_required
def doctor_analytics(request):
    """Analytics and reports for doctors"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    # Basic statistics
    total_appointments = Appointment.objects.filter(doctor=request.user).count()
    completed_appointments = Appointment.objects.filter(
        doctor=request.user, 
        status='completed'
    ).count()
    
    pending_appointments = Appointment.objects.filter(
        doctor=request.user, 
        status='pending',
        appointment_datetime__gte=now
    ).count()
    
    # Weekly statistics
    weekly_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_datetime__gte=seven_days_ago
    ).count()
    
    # Monthly statistics
    monthly_appointments = Appointment.objects.filter(
        doctor=request.user,
        appointment_datetime__gte=thirty_days_ago
    ).count()
    
    monthly_completed = Appointment.objects.filter(
        doctor=request.user,
        status='completed',
        appointment_datetime__gte=thirty_days_ago
    ).count()
    
    # Patient statistics
    total_patients = Appointment.objects.filter(
        doctor=request.user
    ).values('patient').distinct().count()
    
    # Active patients (had appointment in last 30 days)
    active_patients = Appointment.objects.filter(
        doctor=request.user,
        appointment_datetime__gte=thirty_days_ago
    ).values('patient').distinct().count()
    
    # Prescription statistics
    try:
        total_prescriptions = Prescription.objects.filter(doctor=request.user).count()
        monthly_prescriptions = Prescription.objects.filter(
            doctor=request.user,
            created_at__gte=thirty_days_ago
        ).count()
    except:
        total_prescriptions = 0
        monthly_prescriptions = 0
    
    # Calculate rates
    completion_rate = round(
        (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0, 
        1
    )
    
    monthly_completion_rate = round(
        (monthly_completed / monthly_appointments * 100) if monthly_appointments > 0 else 0,
        1
    )
    
    # Recent activity
    recent_appointments = Appointment.objects.filter(
        doctor=request.user
    ).select_related('patient').order_by('-appointment_datetime')[:10]
    
    # Upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        doctor=request.user,
        status='pending',
        appointment_datetime__gte=now
    ).select_related('patient').order_by('appointment_datetime')[:5]
    
    context = {
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
        'weekly_appointments': weekly_appointments,
        'monthly_appointments': monthly_appointments,
        'monthly_completed': monthly_completed,
        'total_patients': total_patients,
        'active_patients': active_patients,
        'total_prescriptions': total_prescriptions,
        'monthly_prescriptions': monthly_prescriptions,
        'recent_appointments': recent_appointments,
        'upcoming_appointments': upcoming_appointments,
        'completion_rate': completion_rate,
        'monthly_completion_rate': monthly_completion_rate,
    }
    
    return render(request, 'users/doctor_analytics.html', context)

@login_required
def doctor_profile(request):
    """Doctor profile and settings"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    if request.method == 'POST':
        # Handle profile updates
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('doctor_profile')
    
    # Get doctor's statistics for profile
    total_appointments = Appointment.objects.filter(doctor=request.user).count()
    total_patients = Appointment.objects.filter(
        doctor=request.user
    ).values('patient').distinct().count()
    
    context = {
        'total_appointments': total_appointments,
        'total_patients': total_patients,
    }
    
    return render(request, 'users/doctor_profile.html', context)


def portal_access(request, role):
    if role == "patient":
        return render(request, "users/dashboard_patient.html")
    elif role == "doctor":
        return render(request, "users/dashboard_doctor.html")
    elif role == "admin":
        return render(request, "users/dashboard_admin.html")
    else:
        return render(request, "users/portal_not_found.html", {"role": role})
    

@login_required
def patient_profile(request):
    """Patient profile management"""
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    if request.method == 'POST':
        # Update profile information
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        # Basic validation
        if not first_name or not last_name:
            messages.error(request, 'First name and last name are required.')
            return redirect('patient_profile')
        
        # Update user information
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        
        # Save phone if you have a profile model
        # request.user.profile.phone = phone
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('patient_profile')
    
    # Get patient statistics for profile
    total_appointments = Appointment.objects.filter(patient=request.user).count()
    completed_visits = Appointment.objects.filter(
        patient=request.user, 
        status='completed'
    ).count()
    total_prescriptions = Prescription.objects.filter(
        appointment__patient=request.user
    ).count()
    
    context = {
        'total_appointments': total_appointments,
        'completed_visits': completed_visits,
        'total_prescriptions': total_prescriptions,
    }
    
    return render(request, 'users/patient_profile.html', context)

@login_required
def patient_medical_history(request):
    """Complete medical history for patient"""
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    # All completed appointments
    medical_records = Appointment.objects.filter(
        patient=request.user,
        status='completed'
    ).select_related('doctor').order_by('-appointment_datetime')
    
    # Limit recent consultations for sidebar / summary
    recent_consultations = medical_records[:5]   # only latest 5
    
    # Prescriptions
    all_prescriptions = Prescription.objects.filter(
        appointment__patient=request.user
    ).select_related('doctor', 'appointment').order_by('-date_issued')
    
    # Pagination
    paginator = Paginator(medical_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'medical_records': page_obj,
        'prescriptions': all_prescriptions,
        'recent_consultations': recent_consultations,
        'total_visits': medical_records.count(),
        'total_prescriptions': all_prescriptions.count(),
    }
    return render(request, 'users/patient_medical_history.html', context)



@login_required
def patient_prescriptions(request):
    """View all prescriptions with filtering"""
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    # Get all prescriptions
    prescriptions = Prescription.objects.filter(
        appointment__patient=request.user
    ).select_related('doctor', 'appointment').order_by('-date_issued')
    
    # Filter by date range if requested
    date_filter = request.GET.get('date_filter')
    if date_filter:
        now = timezone.now()
        if date_filter == 'week':
            start_date = now - timedelta(days=7)
            prescriptions = prescriptions.filter(date_issued__gte=start_date)
        elif date_filter == 'month':
            start_date = now - timedelta(days=30)
            prescriptions = prescriptions.filter(date_issued__gte=start_date)
        elif date_filter == 'year':
            start_date = now - timedelta(days=365)
            prescriptions = prescriptions.filter(date_issued__gte=start_date)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        prescriptions = prescriptions.filter(
            Q(medicine__icontains=search_query) |
            Q(doctor__first_name__icontains=search_query) |
            Q(doctor__last_name__icontains=search_query) |
            Q(instructions__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(prescriptions, 10)  # Show 10 prescriptions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'prescriptions': page_obj,
        'search_query': search_query,
        'date_filter': date_filter,
        'total_prescriptions': prescriptions.count(),
    }
    
    # Render the dedicated prescriptions template
    return render(request, 'users/patient_prescriptions.html', context)


@login_required
def download_prescription(request, prescription_id):
    """Download prescription as PDF"""
    if request.user.role != 'patient':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    prescription = get_object_or_404(
        Prescription, 
        id=prescription_id, 
        appointment__patient=request.user
    )
    
    # Simple text response for now - you can integrate with reportlab for PDF
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="prescription_{prescription.id}.txt"'
    
    content = f"""
PRESCRIPTION
============

Patient: {request.user.get_full_name() or request.user.username}
Doctor: Dr. {prescription.doctor.get_full_name() or prescription.doctor.username}
Date: {prescription.date_issued.strftime('%B %d, %Y')}

Medicine: {prescription.medicine}
Dosage: {prescription.dosage or 'As prescribed'}

Instructions:
{prescription.instructions}

---
Generated on {timezone.now().strftime('%B %d, %Y at %I:%M %p')}
    """
    
    response.write(content)
    return response


@login_required
def patient_appointments_ajax(request):
    """AJAX endpoint for filtering appointments"""
    if request.user.role != 'patient':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    status_filter = request.GET.get('status', 'all')
    
    appointments = Appointment.objects.filter(
        patient=request.user
    ).select_related('doctor').order_by('-appointment_datetime')
    
    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)
    
    appointments_data = []
    for appt in appointments:
        appointments_data.append({
            'id': appt.id,
            'doctor_name': f"Dr. {appt.doctor.get_full_name() or appt.doctor.username}",
            'date': appt.appointment_datetime.strftime('%B %d, %Y'),
            'time': appt.appointment_datetime.strftime('%I:%M %p'),
            'type': appt.get_appointment_type_display(),
            'status': appt.status,
            'symptoms': appt.symptoms or '',
            'notes': appt.notes or '',
            'phone': appt.phone or '',
            'can_reschedule': appt.status == 'pending',
            'can_cancel': appt.status == 'pending',
        })
    
    return JsonResponse({
        'appointments': appointments_data,
        'count': len(appointments_data)
    })

@login_required
def patient_notifications(request):
    """Get patient notifications"""
    if request.user.role != 'patient':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    now = timezone.now()
    
    # Upcoming appointments (within next 24 hours)
    upcoming = Appointment.objects.filter(
        patient=request.user,
        status='pending',
        appointment_datetime__gte=now,
        appointment_datetime__lte=now + timedelta(hours=24)
    ).count()
    
    # Overdue appointments
    overdue = Appointment.objects.filter(
        patient=request.user,
        status='pending',
        appointment_datetime__lt=now
    ).count()
    
    notifications = []
    
    if upcoming > 0:
        notifications.append({
            'type': 'info',
            'message': f'You have {upcoming} appointment{"s" if upcoming > 1 else ""} in the next 24 hours.',
            'icon': 'fa-bell'
        })
    
    if overdue > 0:
        notifications.append({
            'type': 'warning',
            'message': f'You have {overdue} overdue appointment{"s" if overdue > 1 else ""}.',
            'icon': 'fa-exclamation-triangle'
        })
    
    return JsonResponse({
        'notifications': notifications,
        'count': len(notifications)
    })




@login_required
def admin_analytics(request):
    """Comprehensive analytics dashboard for admin"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    year_ago = now - timedelta(days=365)
    
    # ===== USER GROWTH ANALYTICS =====
    # Total users by role
    total_doctors = User.objects.filter(role='doctor').count()
    total_patients = User.objects.filter(role='patient').count()
    total_admins = User.objects.filter(role='admin').count()
    total_users = total_doctors + total_patients + total_admins
    
    # New users this month
    new_users_this_month = User.objects.filter(
        date_joined__gte=thirty_days_ago
    ).count()
    
    new_patients_this_month = User.objects.filter(
        role='patient',
        date_joined__gte=thirty_days_ago
    ).count()
    
    new_doctors_this_month = User.objects.filter(
        role='doctor',
        date_joined__gte=thirty_days_ago
    ).count()
    
    # Weekly user registration data for chart
    weekly_registrations = User.objects.filter(
        date_joined__gte=now - timedelta(days=84)  # 12 weeks
    ).annotate(
        week=TruncWeek('date_joined')
    ).values('week').annotate(
        count=Count('id')
    ).order_by('week')
    
    # Monthly user growth for the past year
    monthly_growth = User.objects.filter(
        date_joined__gte=year_ago
    ).annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(
        total_users=Count('id'),
        doctors=Count('id', filter=Q(role='doctor')),
        patients=Count('id', filter=Q(role='patient'))
    ).order_by('month')
    
    # ===== APPOINTMENT ANALYTICS =====
    total_appointments = Appointment.objects.count()
    completed_appointments = Appointment.objects.filter(status='completed').count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    cancelled_appointments = Appointment.objects.filter(status='cancelled').count()
    
    # Monthly appointment trends
    monthly_appointments = Appointment.objects.filter(
        appointment_datetime__gte=year_ago
    ).annotate(
        month=TruncMonth('appointment_datetime')
    ).values('month').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        pending=Count('id', filter=Q(status='pending'))
    ).order_by('month')
    
    # Daily appointments for the last 30 days
    daily_appointments = Appointment.objects.filter(
        appointment_datetime__gte=thirty_days_ago
    ).annotate(
        date=TruncDate('appointment_datetime')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # ===== PRESCRIPTION ANALYTICS =====
    try:
        total_prescriptions = Prescription.objects.count()
        monthly_prescriptions = Prescription.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        # Top prescribed medicines
        top_medicines = Prescription.objects.values('medicine').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Prescription trends
        prescription_trends = Prescription.objects.filter(
            created_at__gte=year_ago
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')
        
    except:
        total_prescriptions = 0
        monthly_prescriptions = 0
        top_medicines = []
        prescription_trends = []
    
    # ===== PERFORMANCE METRICS =====
    # Doctor utilization
    doctor_performance = User.objects.filter(role='doctor').annotate(
        total_appointments=Count('appointments_as_doctor'),
        completed_appointments=Count(
            'appointments_as_doctor', 
            filter=Q(appointments_as_doctor__status='completed')
        ),
        total_prescriptions=Count('prescriptions')
    ).order_by('-total_appointments')
    
    # Patient engagement
    active_patients = User.objects.filter(
        role='patient',
        appointments_as_patient__appointment_datetime__gte=thirty_days_ago
    ).distinct().count()
    
    # Conversion rates
    appointment_completion_rate = round(
        (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0,
        2
    )
    
    # ===== RECENT ACTIVITY =====
    recent_users = User.objects.exclude(role='admin').order_by('-date_joined')[:10]
    recent_appointments = Appointment.objects.select_related(
        'patient', 'doctor'
    ).order_by('-created_at')[:10]
    
    # ===== GROWTH CALCULATIONS =====
    # Calculate growth percentages
    previous_month_start = thirty_days_ago - timedelta(days=30)
    previous_month_users = User.objects.filter(
        date_joined__gte=previous_month_start,
        date_joined__lt=thirty_days_ago
    ).count()
    
    user_growth_rate = 0
    if previous_month_users > 0:
        user_growth_rate = round(
            ((new_users_this_month - previous_month_users) / previous_month_users * 100),
            2
        )
    
    # Prepare chart data as JSON
    weekly_chart_data = json.dumps([
        {
            'week': reg['week'].strftime('%Y-%m-%d') if reg['week'] else '',
            'count': reg['count']
        }
        for reg in weekly_registrations
    ])
    
    monthly_chart_data = json.dumps([
        {
            'month': growth['month'].strftime('%Y-%m-%d') if growth['month'] else '',
            'total_users': growth['total_users'],
            'doctors': growth['doctors'],
            'patients': growth['patients']
        }
        for growth in monthly_growth
    ])
    
    appointment_chart_data = json.dumps([
        {
            'month': appt['month'].strftime('%Y-%m-%d') if appt['month'] else '',
            'total': appt['total'],
            'completed': appt['completed'],
            'pending': appt['pending']
        }
        for appt in monthly_appointments
    ])
    
    daily_appointment_data = json.dumps([
        {
            'date': appt['date'].strftime('%Y-%m-%d') if appt['date'] else '',
            'count': appt['count']
        }
        for appt in daily_appointments
    ])
    
    context = {
        # User metrics
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_patients': total_patients,
        'total_admins': total_admins,
        'new_users_this_month': new_users_this_month,
        'new_patients_this_month': new_patients_this_month,
        'new_doctors_this_month': new_doctors_this_month,
        'user_growth_rate': user_growth_rate,
        'active_patients': active_patients,
        
        # Appointment metrics
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
        'cancelled_appointments': cancelled_appointments,
        'appointment_completion_rate': appointment_completion_rate,
        
        # Prescription metrics
        'total_prescriptions': total_prescriptions,
        'monthly_prescriptions': monthly_prescriptions,
        'top_medicines': top_medicines,
        
        # Performance data
        'doctor_performance': doctor_performance,
        
        # Recent activity
        'recent_users': recent_users,
        'recent_appointments': recent_appointments,
        
        # Chart data
        'weekly_chart_data': weekly_chart_data,
        'monthly_chart_data': monthly_chart_data,
        'appointment_chart_data': appointment_chart_data,
        'daily_appointment_data': daily_appointment_data,
    }
    
    return render(request, 'users/admin_analytics.html', context)

@login_required
def admin_reports(request):
    """Detailed reports for admin"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    # Date range filtering
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date() - timedelta(days=30)
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()
    
    # Users registered in date range
    users_in_range = User.objects.filter(
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date
    )
    
    # Appointments in date range
    appointments_in_range = Appointment.objects.filter(
        appointment_datetime__date__gte=start_date,
        appointment_datetime__date__lte=end_date
    )
    
    # Detailed statistics
    report_data = {
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'users': {
            'total_registered': users_in_range.count(),
            'doctors': users_in_range.filter(role='doctor').count(),
            'patients': users_in_range.filter(role='patient').count(),
            'daily_breakdown': users_in_range.annotate(
                date=TruncDate('date_joined')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
        },
        'appointments': {
            'total_scheduled': appointments_in_range.count(),
            'completed': appointments_in_range.filter(status='completed').count(),
            'pending': appointments_in_range.filter(status='pending').count(),
            'cancelled': appointments_in_range.filter(status='cancelled').count(),
            'daily_breakdown': appointments_in_range.annotate(
                date=TruncDate('appointment_datetime')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
        }
    }
    
    # Export functionality
    if request.GET.get('export') == 'json':
        response = HttpResponse(
            json.dumps(report_data, default=str, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="clinic_report_{start_date}_to_{end_date}.json"'
        return response
    
    context = {
        'report_data': report_data,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'users/admin_reports.html', context)

@login_required
def admin_user_analytics(request):
    """Detailed user analytics for admin"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    now = timezone.now()
    
    # User engagement metrics
    # Active users (logged in within last 30 days)
    # Note: You'll need to track last_login or create a login tracking system
    
    # Most active patients (by appointment count)
    most_active_patients = User.objects.filter(
        role='patient'
    ).annotate(
        appointment_count=Count('appointments_as_patient')
    ).order_by('-appointment_count')[:10]
    
    # Doctor productivity
    doctor_productivity = User.objects.filter(
        role='doctor'
    ).annotate(
        total_appointments=Count('appointments_as_doctor'),
        completed_this_month=Count(
            'appointments_as_doctor',
            filter=Q(
                appointments_as_doctor__status='completed',
                appointments_as_doctor__appointment_datetime__gte=now - timedelta(days=30)
            )
        ),
        total_prescriptions=Count('prescriptions')
    ).order_by('-total_appointments')
    
    # User registration patterns
    registration_by_day = User.objects.filter(
        date_joined__gte=now - timedelta(days=30)
    ).annotate(
        day=TruncDate('date_joined')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # User demographics (if you have additional profile fields)
    user_role_distribution = User.objects.values('role').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'most_active_patients': most_active_patients,
        'doctor_productivity': doctor_productivity,
        'registration_by_day': list(registration_by_day),
        'user_role_distribution': list(user_role_distribution),
    }
    
    return render(request, 'users/admin_user_analytics.html', context)

@login_required
def admin_system_health(request):
    """System health and performance metrics"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    now = timezone.now()
    
    # System health metrics
    health_metrics = {
        'database_stats': {
            'total_records': (
                User.objects.count() + 
                Appointment.objects.count() + 
                Prescription.objects.count()
            ),
            'users_table': User.objects.count(),
            'appointments_table': Appointment.objects.count(),
            'prescriptions_table': Prescription.objects.count(),
        },
        'recent_activity': {
            'registrations_today': User.objects.filter(
                date_joined__date=now.date()
            ).count(),
            'appointments_today': Appointment.objects.filter(
                appointment_datetime__date=now.date()
            ).count(),
            'prescriptions_today': Prescription.objects.filter(
                created_at__date=now.date()
            ).count() if hasattr(Prescription, 'created_at') else 0,
        },
        'system_usage': {
            'peak_appointment_day': Appointment.objects.annotate(
                day=TruncDate('appointment_datetime')
            ).values('day').annotate(
                count=Count('id')
            ).order_by('-count').first(),
            'busiest_doctor': User.objects.filter(
                role='doctor'
            ).annotate(
                appointment_count=Count('appointments_as_doctor')
            ).order_by('-appointment_count').first(),
        }
    }
    
    # Error tracking (you can expand this based on your error logging)
    recent_errors = []  # Add your error tracking logic here
    
    # Performance alerts
    alerts = []
    
    # Check for potential issues
    overdue_appointments = Appointment.objects.filter(
        status='pending',
        appointment_datetime__lt=now
    ).count()
    
    if overdue_appointments > 10:
        alerts.append({
            'type': 'warning',
            'message': f'{overdue_appointments} overdue appointments need attention',
            'action_url': '/admin/appointments/appointment/?status=pending'
        })
    
    inactive_doctors = User.objects.filter(
        role='doctor'
    ).annotate(
        recent_appointments=Count(
            'appointments_as_doctor',
            filter=Q(appointments_as_doctor__appointment_datetime__gte=now - timedelta(days=30))
        )
    ).filter(recent_appointments=0).count()
    
    if inactive_doctors > 0:
        alerts.append({
            'type': 'info',
            'message': f'{inactive_doctors} doctors have no appointments in the last 30 days',
            'action_url': '/admin/users/user/?role=doctor'
        })
    
    context = {
        'health_metrics': health_metrics,
        'recent_errors': recent_errors,
        'alerts': alerts,
        'overdue_appointments': overdue_appointments,
        'inactive_doctors': inactive_doctors,
    }
    
    return render(request, 'users/admin_system_health.html', context)

@login_required 
def admin_export_data(request):
    """Export system data in various formats"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    export_type = request.GET.get('type', 'users')
    format_type = request.GET.get('format', 'json')
    
    if export_type == 'users':
        data = list(User.objects.values(
            'id', 'username', 'first_name', 'last_name', 
            'email', 'role', 'date_joined', 'is_active'
        ))
    elif export_type == 'appointments':
        data = list(Appointment.objects.select_related(
            'patient', 'doctor'
        ).values(
            'id', 'patient__username', 'doctor__username',
            'appointment_datetime', 'appointment_type', 'status',
            'symptoms', 'notes', 'created_at'
        ))
    elif export_type == 'prescriptions':
        data = list(Prescription.objects.select_related(
            'doctor', 'appointment__patient'
        ).values(
            'id', 'doctor__username', 'appointment__patient__username',
            'medicine', 'dosage', 'instructions', 'date_issued'
        ))
    else:
        return JsonResponse({'error': 'Invalid export type'}, status=400)
    
    if format_type == 'json':
        response = HttpResponse(
            json.dumps(data, default=str, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{export_type}_export.json"'
        return response
    
    # Add CSV export if needed
    elif format_type == 'csv':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_export.csv"'
        
        if data:
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return response
    
    return JsonResponse({'error': 'Invalid format'}, status=400)


# Add these three views to your users/views.py file

@login_required
def admin_users_list(request):
    """Admin view to list and manage users"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    users = User.objects.exclude(role='admin').order_by('-date_joined')
    
    # Apply filters
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_users': User.objects.exclude(role='admin').count(),
        'total_doctors': User.objects.filter(role='doctor').count(),
        'total_patients': User.objects.filter(role='patient').count(),
        'active_users': User.objects.filter(is_active=True).exclude(role='admin').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'stats': stats,
    }
    
    return render(request, 'users/admin_users_list.html', context)

@login_required
def admin_appointments_list(request):
    """Admin view to list and manage appointments"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    doctor_filter = request.GET.get('doctor', '')
    
    # Base queryset
    appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-appointment_datetime')
    
    # Apply filters
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    if date_filter:
        if date_filter == 'today':
            appointments = appointments.filter(appointment_datetime__date=timezone.now().date())
        elif date_filter == 'tomorrow':
            tomorrow = timezone.now().date() + timedelta(days=1)
            appointments = appointments.filter(appointment_datetime__date=tomorrow)
        elif date_filter == 'this_week':
            start_week = timezone.now().date() - timedelta(days=timezone.now().weekday())
            end_week = start_week + timedelta(days=6)
            appointments = appointments.filter(appointment_datetime__date__range=[start_week, end_week])
    
    if doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)
    
    # Pagination
    paginator = Paginator(appointments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_appointments': Appointment.objects.count(),
        'pending': Appointment.objects.filter(status='pending').count(),
        'completed': Appointment.objects.filter(status='completed').count(),
        'cancelled': Appointment.objects.filter(status='cancelled').count(),
        'today': Appointment.objects.filter(appointment_datetime__date=timezone.now().date()).count(),
    }
    
    # Get doctors for filter dropdown
    doctors = User.objects.filter(role='doctor').order_by('first_name')
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'doctor_filter': doctor_filter,
        'stats': stats,
        'doctors': doctors,
    }
    
    return render(request, 'users/admin_appointments_list.html', context)

@login_required
def admin_prescriptions_list(request):
    """Admin view to list and manage prescriptions"""
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('login')
    
    # Get filter parameters
    date_filter = request.GET.get('date', '')
    doctor_filter = request.GET.get('doctor', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset - adjust based on your Prescription model
    try:
        prescriptions = Prescription.objects.select_related('doctor', 'appointment__patient').order_by('-date_issued')
        
        # Apply filters
        if date_filter:
            if date_filter == 'today':
                prescriptions = prescriptions.filter(date_issued=timezone.now().date())
            elif date_filter == 'this_week':
                start_week = timezone.now().date() - timedelta(days=timezone.now().weekday())
                end_week = start_week + timedelta(days=6)
                prescriptions = prescriptions.filter(date_issued__range=[start_week, end_week])
            elif date_filter == 'this_month':
                prescriptions = prescriptions.filter(date_issued__month=timezone.now().month)
        
        if doctor_filter:
            prescriptions = prescriptions.filter(doctor_id=doctor_filter)
        
        if search_query:
            prescriptions = prescriptions.filter(
                Q(medicine__icontains=search_query) |
                Q(appointment__patient__first_name__icontains=search_query) |
                Q(appointment__patient__last_name__icontains=search_query) |
                Q(doctor__first_name__icontains=search_query) |
                Q(doctor__last_name__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(prescriptions, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Statistics
        stats = {
            'total_prescriptions': Prescription.objects.count(),
            'today': Prescription.objects.filter(date_issued=timezone.now().date()).count(),
            'this_week': Prescription.objects.filter(
                date_issued__gte=timezone.now().date() - timedelta(days=7)
            ).count(),
            'this_month': Prescription.objects.filter(
                date_issued__month=timezone.now().month
            ).count(),
        }
        
    except Exception as e:
        # Handle case where Prescription model might not exist or have different fields
        page_obj = None
        stats = {
            'total_prescriptions': 0,
            'today': 0,
            'this_week': 0,
            'this_month': 0,
        }
        messages.warning(request, "Prescription data unavailable. Please check your model configuration.")
    
    # Get doctors for filter dropdown
    doctors = User.objects.filter(role='doctor').order_by('first_name')
    
    context = {
        'page_obj': page_obj,
        'date_filter': date_filter,
        'doctor_filter': doctor_filter,
        'search_query': search_query,
        'stats': stats,
        'doctors': doctors,
    }
    
    return render(request, 'users/admin_prescriptions_list.html', context)


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view"""
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Reset Password'
        return context

class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Password reset done view"""
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset confirm view"""
    form_class = CustomSetPasswordForm
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Password reset complete view"""
    template_name = 'users/password_reset_complete.html'