from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('collector', 'Collector'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    address = models.TextField(blank=True, null=True)
    eco_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.username} ({self.role})"
    def get_level(self):
        """Return a fun title based on eco points"""
        if self.eco_points >= 200:
            return "🌎 Planet Protector"
        elif self.eco_points >= 100:
            return "🍃 Green Hero"
        elif self.eco_points >= 50:
            return "🌱 Eco Starter"
        else:
            return "♻️ New Recycler"

class WasteRequest(models.Model):
    WASTE_TYPES = (
        ('Plastic', 'Plastic'),
        ('Paper', 'Paper'),
        ('Metal', 'Metal'),
        ('Organic', 'Organic'),
    )
    STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Assigned', 'Assigned'),
    ('Collected', 'Collected'),
    ('Recycled', 'Recycled'),
]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)
    quantity = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    assigned_collector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.waste_type} - {self.user.username}"
    


class RecyclingRecord(models.Model):
    request = models.ForeignKey(WasteRequest, on_delete=models.CASCADE)
    recycled_items = models.TextField()
    recycled_weight = models.FloatField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Recycled: {self.request.user.username}"

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    rating = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.user.username}"
    
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    reply = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(upload_to='complaints/', null=True, blank=True)

    def __str__(self):
        return f"{self.subject} ({self.status})"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
class Payment(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - ₹{self.amount} ({self.status})"
