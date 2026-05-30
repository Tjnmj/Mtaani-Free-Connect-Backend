from django.db import models
from django.contrib.auth.models import User

class Package(models.Model):
    name        = models.CharField(max_length=50)
    duration_h  = models.IntegerField()          
    price_ksh   = models.IntegerField()          
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - KSH {self.price_ksh}"

class Router(models.Model):
    name       = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    is_online  = models.BooleanField(default=False)
    last_seen  = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} | {'Online' if self.is_online else 'Offline'}"


class Session(models.Model):
    STATUS = [
        ('pending',   'Pending'),
        ('active',    'Active'),
        ('expired',   'Expired'),
        ('cancelled', 'Cancelled'),
    ]
   
    phone        = models.CharField(max_length=15)
    package      = models.ForeignKey(Package, on_delete=models.PROTECT)
    status       = models.CharField(max_length=12, choices=STATUS, default='pending')
    activated_at = models.DateTimeField(null=True, blank=True)
    expires_at   = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone} | {self.package.name} | {self.status}"


class Payment(models.Model):
    session        = models.OneToOneField(Session, on_delete=models.CASCADE)
    mpesa_code     = models.CharField(max_length=20, blank=True)
    checkout_req_id= models.CharField(max_length=100, blank=True)
    amount         = models.DecimalField(max_digits=8, decimal_places=2)
    phone          = models.CharField(max_length=15)
    paid_at        = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.phone} | {self.amount} | {self.mpesa_code}"


class Voucher(models.Model):
    code       = models.CharField(max_length=20, unique=True)
    package    = models.ForeignKey(Package, on_delete=models.PROTECT)
    is_used    = models.BooleanField(default=False)
    used_at    = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} | {'Used' if self.is_used else 'Available'}"


class Reconnect(models.Model):
    mpesa_code  = models.CharField(max_length=20)
    phone       = models.CharField(max_length=15)
    reconnected_at = models.DateTimeField(auto_now_add=True)
    session     = models.ForeignKey(Session, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.phone} | {self.mpesa_code}"

class FreeTrial(models.Model):
    device_id  = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.device_id