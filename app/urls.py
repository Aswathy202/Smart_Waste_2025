from django.urls import path
from . import views

urlpatterns = [
     path('', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('about/', views.about_view, name='about'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('citizen/dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('citizen/new-request/', views.new_waste_request, name='new_request'),
    path('collector/dashboard/', views.collector_dashboard, name='collector_dashboard'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('citizen/dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('collector/update-status/<int:request_id>/', views.update_request_status, name='update_request_status'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('my-feedbacks/', views.my_feedbacks, name='my_feedbacks'),
    path('feedback/<int:feedback_id>/edit/', views.edit_feedback, name='edit_feedback'),
    path('feedback/<int:feedback_id>/delete/', views.delete_feedback, name='delete_feedback'),
    path('citizen/complaint/', views.citizen_complaint, name='citizen_complaint'),
    path('complaints/', views.admin_complaints, name='admin_complaints'),
    path('collector_complaints/', views.collector_complaints, name='collector_complaints'),
    path('smartadmin/export/requests/', views.export_requests_csv, name='export_requests_csv'),
    path('smartadmin/export/complaints/', views.export_complaints_csv, name='export_complaints_csv'),
    path('contact/', views.contact_view, name='contact'),
    path('make_payment/', views.make_payment, name='make_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment_history/', views.payment_history, name='payment_history'),


]
