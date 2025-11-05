from django.contrib import admin
from .models import User, WasteRequest, RecyclingRecord, Feedback,Complaint,Notification,Payment

admin.site.register(User)
admin.site.register(WasteRequest)
admin.site.register(RecyclingRecord)
admin.site.register(Feedback)
admin.site.register(Complaint)
admin.site.register(Notification)
admin.site.register(Payment)
