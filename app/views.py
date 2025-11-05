from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import WasteRequest,User,Feedback,Complaint,Payment
from .forms import RegisterForm,FeedbackForm,ComplaintForm
import json
import csv
from django.db.models import Sum
from django.http import HttpResponse
from geopy.geocoders import Nominatim
from django.core.mail import send_mail
from django.conf import settings
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt




def home_view(request):
    return render(request, 'home.html')




def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! Please log in.")
            return redirect('login')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def about_view(request):
    return render(request, 'about.html')



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.role == 'citizen':
                return redirect('home')
            elif user.role == 'collector':
                return redirect('home')
            else:
                return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You’ve been logged out.")
    return redirect('login')

@login_required
def citizen_dashboard(request):
    requests = WasteRequest.objects.filter(user=request.user)
    return render(request, 'citizen_dashboard.html', {'requests': requests})

@login_required
def new_waste_request(request):
    if request.method == 'POST':
        waste_type = request.POST['waste_type']
        quantity = request.POST['quantity']
        location = request.POST['location']
        WasteRequest.objects.create(
            user=request.user, waste_type=waste_type, quantity=quantity, location=location
        )
        messages.success(request, "Waste pickup request submitted.")
        return redirect('citizen_dashboard')
    return render(request, 'new_request.html')

@login_required
def collector_dashboard(request):
    # Only collectors can access this page
    if request.user.role != 'collector':
        messages.error(request, "Access denied.")
        return redirect('home')

    collector = request.user
    assigned_requests = WasteRequest.objects.filter(assigned_collector=collector)

    # Handle status updates
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        new_status = request.POST.get('status')
        waste_request = get_object_or_404(WasteRequest, id=request_id, assigned_collector=request.user)
        waste_request.status = new_status
        waste_request.save()
        print(f"🧾 Status updated for request {request_id}: {new_status}")

        # 🌱 Award eco points to the citizen when marked as recycled
        if new_status == "Recycled":
            waste_request.user.eco_points += 20
            waste_request.user.save()

        messages.success(request, f"Status updated to '{new_status}' successfully.")
        return redirect('collector_dashboard')

    # Summary counts
    summary = {
        "total": assigned_requests.count(),
        "pending": assigned_requests.filter(status="Pending").count(),
        "collected": assigned_requests.filter(status="Collected").count(),
        "recycled": assigned_requests.filter(status="Recycled").count(),
    }

    # Map setup
    geolocator = Nominatim(user_agent="smartwaste")
    map_data = []
    for req in assigned_requests:
        location = None
        try:
            location = geolocator.geocode(req.location, timeout=10)
        except Exception:
            pass

        if location:
            lat, lon = location.latitude, location.longitude
        else:
            lat, lon = 8.5241, 76.9366  # Default Trivandrum

        map_data.append({
            "latitude": lat,
            "longitude": lon,
            "citizen": req.user.username,
            "waste_type": req.waste_type,
            "status": req.status,
            "location": req.location,
        })

    context = {
        "assigned_requests": assigned_requests,
        "summary": summary,
        "map_data": json.dumps(map_data),
    }
    return render(request, "collector/collector_dashboard.html", context)

@login_required
@login_required
def admin_dashboard(request):
    # Restrict access
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('home')

    # Fetch all requests (most recent first)
    all_requests = WasteRequest.objects.select_related('user', 'assigned_collector').order_by('-created_at')

    # Get all collectors for dropdown
    collectors = User.objects.filter(role='collector')

    # Handle collector assignment
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        collector_id = request.POST.get('collector_id')

        try:
            waste_request = WasteRequest.objects.get(id=request_id)
            collector = User.objects.get(id=collector_id, role='collector')
            waste_request.assigned_collector = collector
            waste_request.status = 'Assigned'
            waste_request.save()
            messages.success(request, f"Collector '{collector.username}' assigned successfully.")
        except (WasteRequest.DoesNotExist, User.DoesNotExist):
            messages.error(request, "Something went wrong while assigning the collector.")
        return redirect('admin_dashboard')

    # ✅ Summary for waste requests
    summary = {
        'total': all_requests.count(),
        'pending': all_requests.filter(status='Pending').count(),
        'collected': all_requests.filter(status='Collected').count(),
        'recycled': all_requests.filter(status='Recycled').count(),
    }

    # ✅ Complaint stats
    pending_complaints = Complaint.objects.filter(status='Pending').count()
    resolved_complaints = Complaint.objects.filter(status='Resolved').count()

    # ✅ Payment stats
    total_payments = Payment.objects.filter(status='Success').count()
    total_amount = Payment.objects.filter(status='Success').aggregate(Sum('amount'))['amount__sum'] or 0

    # ✅ Context for template
    context = {
        'requests': all_requests,
        'collectors': collectors,
        'summary': summary,
        'pending_requests': summary['pending'],
        'collected_requests': summary['collected'],
        'recycled_requests': summary['recycled'],
        'pending_complaints': pending_complaints,
        'resolved_complaints': resolved_complaints,
        'total_payments': total_payments,
        'total_amount': total_amount,
    }

    return render(request, 'admin/admin_dashboard.html', context)


@login_required
def citizen_dashboard(request):
    if request.user.role != 'citizen':
        messages.error(request, "Access denied.")
        return redirect('home')

    # Handle new request form
    if request.method == 'POST':
        waste_type = request.POST.get('waste_type')
        quantity = request.POST.get('quantity')
        location = request.POST.get('location')

        WasteRequest.objects.create(
            user=request.user,
            waste_type=waste_type,
            quantity=quantity,
            location=location,
        )
        messages.success(request, "Your waste pickup request has been submitted.")
        request.user.eco_points += 10  # Earn 10 points
        request.user.save()
        messages.success(request, "Waste pickup request submitted! +10 eco points 🌱")
        return redirect('citizen_dashboard')

    # Fetch user's requests
    my_requests = WasteRequest.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'requests': my_requests
    }

    return render(request, 'citizen/citizen_dashboard.html', context)

def update_request_status(request, request_id):
    if request.method == 'POST':
        req = get_object_or_404(WasteRequest, id=request_id)
        new_status = request.POST.get('status')
        req.status = new_status
        req.save()
        return redirect('collector_dashboard')
    
def feedback_view(request):
    feedback_list = Feedback.objects.all().order_by('-created_at')
    form = None

    # Allow only citizens to submit feedback
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'citizen':
        if request.method == 'POST':
            form = FeedbackForm(request.POST)
            if form.is_valid():
                feedback = form.save(commit=False)
                feedback.user = request.user
                feedback.save()
                messages.success(request, "Thank you for your feedback!")
                return redirect('feedback')
        else:
            form = FeedbackForm()

    context = {'form': form, 'feedback_list': feedback_list}
    return render(request, 'feedback.html', context)

@login_required
def my_feedbacks(request):
    if request.user.role != 'citizen':
        messages.error(request, "Access denied.")
        return redirect('home')

    feedbacks = Feedback.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'citizen/my_feedbacks.html', {'feedbacks': feedbacks})

@login_required
def edit_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id, user=request.user)

    if request.method == 'POST':
        message = request.POST.get('message')
        feedback.message = message
        feedback.save()
        messages.success(request, "Feedback updated successfully.")
        return redirect('my_feedbacks')

    return render(request, 'citizen/edit_feedback.html', {'feedback': feedback})


@login_required
def delete_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, id=feedback_id, user=request.user)
    feedback.delete()
    messages.success(request, "Feedback deleted successfully.")
    return redirect('my_feedbacks')

@login_required
def citizen_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.save()
            messages.success(request, "Complaint submitted successfully!")
    else:
        form = ComplaintForm()

    complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'citizen/complaint.html', {'form': form, 'complaints': complaints})

@login_required
def admin_complaints(request):
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('home')

    complaints = Complaint.objects.all().order_by('-created_at')

    if request.method == 'POST':
        complaint_id = request.POST.get('complaint_id')
        reply_text = request.POST.get('reply')
        status = request.POST.get('status', 'Resolved')

        complaint = get_object_or_404(Complaint, id=complaint_id)
        complaint.reply = reply_text
        complaint.status = status
        complaint.save()
        messages.success(request, f"Reply sent for complaint ID {complaint_id}")
        return redirect('admin_complaints')

    return render(request, 'admin/complaints.html', {'complaints': complaints})

@login_required
def collector_complaints(request):
    # Ensure only collectors can access this page
    if request.user.role != 'collector':
        return redirect('home')  # or any page you want to redirect to

    complaints = Complaint.objects.all().order_by('-created_at')
    return render(request, 'collector/complaints.html', {'complaints': complaints})

@login_required
def export_requests_csv(request):
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('home')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="waste_requests.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Waste Type', 'Status', 'Collector', 'Created At'])

    requests = WasteRequest.objects.all()
    for req in requests:
        writer.writerow([
            req.user.username,
            req.waste_type,
            req.status,
            req.assigned_collector.username if req.assigned_collector else 'Not Assigned',
            req.created_at.strftime('%d-%m-%Y %H:%M')
        ])

    return response


@login_required
def export_complaints_csv(request):
    if request.user.role != 'admin':
        messages.error(request, "Access denied.")
        return redirect('home')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Subject', 'Description', 'Status', 'Reply', 'Created At'])

    complaints = Complaint.objects.all()
    for c in complaints:
        writer.writerow([
            c.user.username,
            c.subject,
            c.description,
            c.status,
            c.reply if c.reply else '',
            c.created_at.strftime('%d-%m-%Y %H:%M')
        ])

    return response

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # (Optional) Send email to admin
        send_mail(
            subject=f"SmartWaste Contact from {name}",
            message=f"Sender: {name}\nEmail: {email}\n\nMessage:\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['admin@smartwaste.com'],  # change to your admin email
            fail_silently=True,
        )

        messages.success(request, "Thank you! Your message has been sent successfully.")
        return redirect('contact')

    return render(request, 'contact.html')

@login_required
def make_payment(request):
    if request.user.role != 'citizen':
        messages.error(request, "Access denied.")
        return redirect('home')

    # Amount per pickup (₹50)
    amount = 50 * 100  # Razorpay works in paise
    client = razorpay.Client(auth=(settings.RZP_KEY_ID, settings.RZP_KEY_SECRET))

    # Create order
    payment_data = {
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1",
    }
    order = client.order.create(payment_data)

    # Save payment record
    Payment.objects.create(
        user=request.user,
        amount=50,
        order_id=order["id"]
    )

    context = {
        "order_id": order["id"],
        "amount": 50,
        "key_id": settings.RZP_KEY_ID,
        "user": request.user,
    }
    return render(request, "citizen/make_payment.html", context)

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get("razorpay_payment_id")
        order_id = request.POST.get("razorpay_order_id")

        payment = Payment.objects.filter(order_id=order_id).first()
        if payment:
            payment.payment_id = payment_id
            payment.status = "Success"
            payment.save()
            payment.user.eco_points += 15  # 🎁 Reward citizen
            payment.user.save()

        messages.success(request, "Payment successful! +15 eco points 🌱")
        return redirect('citizen_dashboard')
    return redirect('home')

@login_required
def payment_history(request):
    if request.user.role != 'citizen':
        messages.error(request, "Access denied.")
        return redirect('home')

    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'citizen/payment_history.html', {'payments': payments})
