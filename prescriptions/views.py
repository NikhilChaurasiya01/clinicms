from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
# Create your views here.
from django.contrib.auth.decorators import login_required
from .models import Prescription
from appointments.models import Appointment
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from users.forms import PrescriptionForm
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied


User = get_user_model()
@login_required
def add_prescription(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    if request.method == "POST":
        details = request.POST["details"]
        Prescription.objects.create(appointment=appointment, doctor=request.user, details=details)
        return redirect("dashboard")
    return render(request, "prescriptions/add.html", {"appointment": appointment})




def edit_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)

    # Only the prescribing doctor can edit
    if prescription.doctor != request.user:
        raise PermissionDenied()

    if request.method == "POST":
        form = PrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            return redirect("dashboard_doctor")
    else:
        form = PrescriptionForm(instance=prescription)

    return render(request, "prescriptions/edit_prescription.html", {"form": form})

@login_required
def list_prescriptions(request):
    """List all prescriptions for the doctor"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    prescriptions = Prescription.objects.filter(
        doctor=request.user
    ).select_related('patient', 'appointment').order_by('-date_issued')
    
    # Filter by search query
    search_query = request.GET.get('q', '')
    if search_query:
        prescriptions = prescriptions.filter(
            Q(patient__username__icontains=search_query) |
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(medication__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        if status_filter == 'active':
            prescriptions = prescriptions.filter(is_active=True)
        elif status_filter == 'expired':
            prescriptions = prescriptions.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(prescriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'prescriptions': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_prescriptions': prescriptions.count()
    }
    
    return render(request, 'users/list.html', context)

@login_required
def active_prescriptions(request):
    """Show only active prescriptions"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    prescriptions = Prescription.objects.filter(
        doctor=request.user,
        is_active=True
    ).select_related('patient', 'appointment').order_by('-date_issued')
    
    # Pagination
    paginator = Paginator(prescriptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'prescriptions': page_obj,
        'title': 'Active Prescriptions',
        'total_prescriptions': prescriptions.count()
    }
    
    return render(request, 'users/active.html', context)

@login_required
def prescription_templates(request):
    """Manage prescription templates for quick prescribing"""
    if request.user.role != 'doctor':
        messages.error(request, "Access denied.")
        return redirect('dashboard_doctor')
    
    # You might want to create a PrescriptionTemplate model for this
    # For now, let's show commonly prescribed medications
    common_prescriptions = Prescription.objects.filter(
        doctor=request.user
    ).values('medicine').annotate(
        count=Count('medicine')
    ).order_by('-count')[:20]
    
    context = {
        'common_prescriptions': common_prescriptions,
    }
    
    return render(request, 'users/template.html', context)



def print_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    
    # Only doctor or patient can print
    if prescription.doctor != request.user and prescription.patient != request.user:
        raise PermissionDenied()
    
    return render(request, 'prescriptions/print_prescription.html', {
        'prescription': prescription,
    })
