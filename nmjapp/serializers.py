from rest_framework import serializers
from django.contrib.auth.models import User
from .models import FreeTrial, Package, Payment, Session, Voucher, Reconnect,Router,PPPoEPlan, PPPoEClient, IPPool, PPPoEPayment

#login
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}  

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

#package
class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Package  
        fields = ['id', 'name', 'duration_h', 'price_ksh', 'is_active']

    def create(self, validated_data):
        return Package.objects.create(**validated_data)  

#payment
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment   
        fields = ['id', 'session', 'mpesa_code', 'checkout_req_id', 'amount', 'phone', 'paid_at']

    def create(self, validated_data):
        return Payment.objects.create(**validated_data)  

#session
class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Session   
        fields = ['id', 'phone', 'package', 'status', 'activated_at', 'expires_at', 'created_at']

    def create(self, validated_data):
        return Session.objects.create(**validated_data)  

#voucher
class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Voucher   
        fields = ['id', 'code', 'package', 'is_used', 'used_at', 'created_at']

    def create(self, validated_data):
        return Voucher.objects.create(**validated_data)  

#reconnect
class ReconnectSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Reconnect  
        fields = ['id', 'mpesa_code', 'phone', 'reconnected_at', 'session']

    def create(self, validated_data):
        return Reconnect.objects.create(**validated_data)  
#router
class RouterSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Router
        fields = ['id', 'name', 'ip_address', 'is_online', 'last_seen']

    def create(self, validated_data):
        return Reconnect.objects.create(**validated_data)  
    
class FreeTrialSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FreeTrial
        fields = ['id', 'device_id', 'created_at']

    def create(self, validated_data):
        return Reconnect.objects.create(**validated_data)  

# dashboard
class DashboardStatsSerializer(serializers.Serializer):
    total_users        = serializers.IntegerField()
    active_users       = serializers.IntegerField()
    expired_users      = serializers.IntegerField()
    revenue_today      = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_this_week  = serializers.DecimalField(max_digits=10, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    unused_vouchers    = serializers.IntegerField()
    pending_payments   = serializers.IntegerField()
    routers_online     = serializers.IntegerField()
    routers_total      = serializers.IntegerField()

#ppoe plan
class PPPoEPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PPPoEPlan
        fields = ['id', 'name', 'price_ksh', 'speed_up', 'speed_down', 'duration_days', 'is_active']

class IPPoolSerializer(serializers.ModelSerializer):
    class Meta:
        model  = IPPool
        fields = ['id', 'name', 'subnet', 'gateway', 'created_at']

class PPPoEClientSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    class Meta:
        model  = PPPoEClient
        fields = ['id', 'full_name', 'phone', 'username', 'password', 'plan', 'plan_name', 'ip_pool', 'static_ip', 'status', 'activated_at', 'expires_at', 'created_at']

class PPPoEPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PPPoEPayment
        fields = ['id', 'client', 'phone', 'amount', 'mpesa_code', 'checkout_req_id', 'paid_at', 'created_at']