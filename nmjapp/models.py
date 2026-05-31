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

class PPPoEPlan(models.Model):
    name         = models.CharField(max_length=100)
    price_ksh    = models.IntegerField()
    speed_up     = models.CharField(max_length=20)  
    speed_down   = models.CharField(max_length=20)  
    duration_days= models.IntegerField(default=30)
    is_active    = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - KES {self.price_ksh}"


class IPPool(models.Model):
    name       = models.CharField(max_length=100)
    subnet     = models.CharField(max_length=50)  
    gateway    = models.CharField(max_length=20)  
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subnet}"


class PPPoEClient(models.Model):
    STATUS = [
        ('active',    'Active'),
        ('expired',   'Expired'),
        ('suspended', 'Suspended'),
    ]
    full_name    = models.CharField(max_length=100)
    phone        = models.CharField(max_length=15)
    username     = models.CharField(max_length=50, unique=True)
    password     = models.CharField(max_length=50)
    plan         = models.ForeignKey(PPPoEPlan, on_delete=models.PROTECT)
    ip_pool      = models.ForeignKey(IPPool, on_delete=models.SET_NULL, null=True, blank=True)
    static_ip    = models.GenericIPAddressField(null=True, blank=True)
    status       = models.CharField(max_length=12, choices=STATUS, default='active')
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at   = models.DateTimeField()
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} | {self.plan.name} | {self.status}"


class PPPoEPayment(models.Model):
    client         = models.ForeignKey(PPPoEClient, on_delete=models.CASCADE)
    phone          = models.CharField(max_length=15)
    amount         = models.DecimalField(max_digits=8, decimal_places=2)
    mpesa_code     = models.CharField(max_length=20, blank=True)
    checkout_req_id= models.CharField(max_length=100, blank=True)
    paid_at        = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.username} | {self.amount} | {self.mpesa_code}"

class Reseller(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE)
    phone      = models.CharField(max_length=15)
    business_name = models.CharField(max_length=100)
    balance    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} | KES {self.balance}"


class ResellerTopUp(models.Model):
    reseller       = models.ForeignKey(Reseller, on_delete=models.CASCADE)
    amount         = models.DecimalField(max_digits=8, decimal_places=2)
    mpesa_code     = models.CharField(max_length=20, blank=True)
    checkout_req_id= models.CharField(max_length=100, blank=True)
    paid_at        = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reseller.business_name} | KES {self.amount}"


class ResellerVoucherBatch(models.Model):
    reseller   = models.ForeignKey(Reseller, on_delete=models.CASCADE)
    package    = models.ForeignKey(Package, on_delete=models.PROTECT)
    quantity   = models.IntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reseller.business_name} | {self.quantity} vouchers | {self.package.name}"