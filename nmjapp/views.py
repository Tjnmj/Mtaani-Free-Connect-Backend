from .serializers import UserSerializer, PackageSerializer, PaymentSerializer, SessionSerializer, VoucherSerializer, ReconnectSerializer, RouterSerializer, DashboardStatsSerializer, FreeTrialSerializer,PPPoEPlanSerializer, PPPoEClientSerializer, IPPoolSerializer, PPPoEPaymentSerializer,ResellerSerializer, ResellerTopUpSerializer, ResellerVoucherBatchSerializer
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.utils import timezone
from .models import FreeTrial, Package, Payment, Session, Voucher, Reconnect,Router,PPPoEPlan, PPPoEClient, IPPool, PPPoEPayment,Reseller, ResellerTopUp, ResellerVoucherBatch
from .mpesa import stk_push
from datetime import timedelta 
from datetime import date
from django.db.models import Sum

# User registration
class CreateUserView(generics.CreateAPIView):
    queryset           = User.objects.all()   
    serializer_class   = UserSerializer
    permission_classes = [AllowAny]


#  packages  
class PackageListView(generics.ListAPIView):
    queryset           = Package.objects.filter(is_active=True)
    serializer_class   = PackageSerializer
    permission_classes = [AllowAny]  

class PackageDestroyView(generics.RetrieveDestroyAPIView):
    queryset           = Package.objects.all()
    serializer_class   = PackageSerializer
    permission_classes = [IsAuthenticated]

#payments
class PaymentListView(generics.ListAPIView):
    queryset           = Payment.objects.select_related('session').order_by('-paid_at')
    serializer_class   = PaymentSerializer
    permission_classes = [IsAuthenticated]


class PaymentDestroyView(generics.RetrieveDestroyAPIView):
    queryset           = Payment.objects.all()
    serializer_class   = PaymentSerializer
    permission_classes = [IsAuthenticated]


# Initiate M-Pesa payment 
class InitiatePaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone      = request.data.get('phone', '').strip()
        package_id = request.data.get('package_id')

      
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]

        try:
            package = Package.objects.get(id=package_id, is_active=True)
        except Package.DoesNotExist:
            return Response({"error": "Package not found"}, status=400)

        session = Session.objects.create(phone=phone, package=package)
        result  = stk_push(phone, package.price_ksh, str(session.id))

        if result.get('ResponseCode') == '0':
            Payment.objects.create(
                session         = session,
                phone           = phone,
                amount          = package.price_ksh,
                checkout_req_id = result['CheckoutRequestID'],
            )
            return Response({"session_id": str(session.id)})
        else:
            session.status = 'cancelled'
            session.save()
            return Response({"error": result.get('errorMessage', 'STK push failed')}, status=400)


# Safaricom posts here after payment
class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        body        = request.data.get('Body', {}).get('stkCallback', {})
        result_code = body.get('ResultCode')
        checkout_id = body.get('CheckoutRequestID')

        try:
            payment = Payment.objects.get(checkout_req_id=checkout_id)
            session = payment.session
        except Payment.DoesNotExist:
            return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

        if result_code == 0:
            items      = body.get('CallbackMetadata', {}).get('Item', [])
            mpesa_code = next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), '')
            payment.mpesa_code = mpesa_code
            payment.paid_at    = timezone.now()
            payment.save()
            session.status       = 'active'
            session.activated_at = timezone.now()
            session.expires_at = timezone.now() + timedelta(hours=session.package.duration_h)
            session.save()
        else:
            session.status = 'cancelled'
            session.save()

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


#session
class SessionStatusView(generics.RetrieveAPIView):
    queryset           = Session.objects.all()
    serializer_class   = SessionSerializer
    permission_classes = [AllowAny]


class SessionDestroyView(generics.RetrieveDestroyAPIView):
    queryset           = Session.objects.all()
    serializer_class   = SessionSerializer
    permission_classes = [IsAuthenticated]
  


# Voucher activation
class ActivateVoucherView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code', '').strip().upper()
        try:
            voucher = Voucher.objects.get(code=code, is_used=False)
        except Voucher.DoesNotExist:
            return Response({"error": "Invalid voucher"}, status=400)

        session = Session.objects.create(
            phone    = request.data.get('phone', 'voucher'),
            package  = voucher.package,
            status   = 'active',
            activated_at = timezone.now(),
            expires_at = timezone.now() + timedelta(hours=voucher.package.duration_h)
        )
        voucher.is_used = True
        voucher.used_at = timezone.now()
        voucher.save()
        return Response({"session_id": str(session.id), "status": "active"})

class VoucherListView(generics.ListAPIView):
    queryset           = Voucher.objects.all().order_by('-id')
    serializer_class   = VoucherSerializer
    permission_classes = [IsAuthenticated]


class VoucherDestroyView(generics.RetrieveDestroyAPIView):
    queryset           = Voucher.objects.all()
    serializer_class   = VoucherSerializer
    permission_classes = [IsAuthenticated]


# Reconnect using M-Pesa code
class ReconnectView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('mpesa_code', '').strip().upper()
        try:
            payment = Payment.objects.get(mpesa_code=code)
            session = payment.session
        except Payment.DoesNotExist:
            return Response({"error": "Something went wrong"}, status=404)

        if session.status != 'active':
            return Response({"error": "Invalid Session"}, status=400)

        Reconnect.objects.create(
            mpesa_code = code,
            phone      = session.phone,
            session    = session,
        )
        return Response({"session_id": str(session.id), "status": "active"})
    
# Dashboard stats
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        week_start  = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        stats = {
            'total_users':    Session.objects.count(),
            'active_users':   Session.objects.filter(
                                status='active',
                                expires_at__gt=timezone.now()
                              ).count(),
            'expired_users':  Session.objects.filter(status='expired').count(),

            'revenue_today':      Payment.objects.filter(
                                    paid_at__date=today
                                  ).aggregate(t=Sum('amount'))['t'] or 0,
            'revenue_this_week':  Payment.objects.filter(
                                    paid_at__date__gte=week_start
                                  ).aggregate(t=Sum('amount'))['t'] or 0,
            'revenue_this_month': Payment.objects.filter(
                                    paid_at__date__gte=month_start
                                  ).aggregate(t=Sum('amount'))['t'] or 0,

            'unused_vouchers':  Voucher.objects.filter(is_used=False).count(),
            'pending_payments': Session.objects.filter(status='pending').count(),
            'routers_online':   Router.objects.filter(is_online=True).count(),
            'routers_total':    Router.objects.count(),
        }
        return Response(stats)


# Router 
class RouterListView(generics.ListCreateAPIView):
    queryset           = Router.objects.all()
    serializer_class   = RouterSerializer
    permission_classes = [IsAuthenticated]


class RouterDestroyView(generics.RetrieveDestroyAPIView):
    queryset           = Router.objects.all()
    serializer_class   = RouterSerializer
    permission_classes = [IsAuthenticated]
    
# Hotspot users list
class HotspotUserListView(generics.ListAPIView):
    serializer_class   = SessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Session.objects.select_related('package').order_by('-created_at')
    

#free trial
class FreeTrialView(APIView):
    permission_classes = [AllowAny]
    serializer_class   = FreeTrialSerializer

    def post(self, request):
        device_id = request.data.get('device_id', '').strip()
        if not device_id:
            return Response({"error": "Device ID required"}, status=400)

        if FreeTrial.objects.filter(device_id=device_id).exists():
            return Response({"error": "Free trial already used on this device"}, status=400)

        
        package, _ = Package.objects.get_or_create(
            name='Free Trial',
            defaults={'duration_h': 0, 'price_ksh': 0, 'is_active': False}
        )
        
        session = Session.objects.create(
            phone='free-trial',
            package=package,
            status='active',
            activated_at=timezone.now(),
            expires_at=timezone.now() + timedelta(minutes=3),
        )
        FreeTrial.objects.create(device_id=device_id)
        return Response({"session_id": str(session.id), "status": "active"})
    
#ppoe plans
class PPPoEPlanListView(generics.ListCreateAPIView):
    queryset           = PPPoEPlan.objects.all()
    serializer_class   = PPPoEPlanSerializer
    permission_classes = [IsAuthenticated]

class PPPoEPlanDestroyView(generics.RetrieveDestroyAPIView):
    queryset           = PPPoEPlan.objects.all()
    serializer_class   = PPPoEPlanSerializer
    permission_classes = [IsAuthenticated]

#ip pools
class IPPoolListView(generics.ListCreateAPIView):
    queryset           = IPPool.objects.all()
    serializer_class   = IPPoolSerializer
    permission_classes = [IsAuthenticated]

class IPPoolDestroyView(generics.RetrieveDestroyAPIView):
    queryset           = IPPool.objects.all()
    serializer_class   = IPPoolSerializer
    permission_classes = [IsAuthenticated]

#ppoe clients
class PPPoEClientListView(generics.ListCreateAPIView):
    queryset           = PPPoEClient.objects.select_related('plan').order_by('-created_at')
    serializer_class   = PPPoEClientSerializer
    permission_classes = [IsAuthenticated]

class PPPoEClientDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = PPPoEClient.objects.all()
    serializer_class   = PPPoEClientSerializer
    permission_classes = [IsAuthenticated]

class PPPoEClientStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            client = PPPoEClient.objects.select_related('plan').get(username=username)
        except PPPoEClient.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)
        serializer = PPPoEClientSerializer(client)
        return Response(serializer.data)

class PPPoERenewView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username   = request.data.get('username', '').strip()
        phone      = request.data.get('phone', '').strip()

        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]

        try:
            client = PPPoEClient.objects.select_related('plan').get(username=username)
        except PPPoEClient.DoesNotExist:
            return Response({"error": "Client not found"}, status=404)

        payment = PPPoEPayment.objects.create(
            client = client,
            phone  = phone,
            amount = client.plan.price_ksh,
        )
        result = stk_push(phone, client.plan.price_ksh, f"pppoe-{client.username}")

        if result.get('ResponseCode') == '0':
            payment.checkout_req_id = result['CheckoutRequestID']
            payment.save()
            return Response({"payment_id": payment.id, "message": "STK push sent"})
        else:
            payment.delete()
            return Response({"error": result.get('errorMessage', 'STK push failed')}, status=400)

class PPPoECallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        body        = request.data.get('Body', {}).get('stkCallback', {})
        result_code = body.get('ResultCode')
        checkout_id = body.get('CheckoutRequestID')

        try:
            payment = PPPoEPayment.objects.get(checkout_req_id=checkout_id)
            client  = payment.client
        except PPPoEPayment.DoesNotExist:
            return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

        if result_code == 0:
            items      = body.get('CallbackMetadata', {}).get('Item', [])
            mpesa_code = next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), '')
            payment.mpesa_code = mpesa_code
            payment.paid_at    = timezone.now()
            payment.save()
            client.status     = 'active'
            client.expires_at = timezone.now() + timedelta(days=client.plan.duration_days)
            client.save()

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

class PPPoEVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()
        try:
            client = PPPoEClient.objects.select_related('plan').get(username=username)
        except PPPoEClient.DoesNotExist:
            return Response({"error": "Account not found"}, status=404)
        
        if client.password != password:
            return Response({"error": "Incorrect password"}, status=401)
        
        serializer = PPPoEClientSerializer(client)
        return Response(serializer.data)
    
# Reseller 
class ResellerCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username      = request.data.get('username')
        password      = request.data.get('password')
        phone         = request.data.get('phone')
        business_name = request.data.get('business_name')

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=400)

        user = User.objects.create_user(username=username, password=password)
        reseller = Reseller.objects.create(
            user=user,
            phone=phone,
            business_name=business_name,
        )
        return Response(ResellerSerializer(reseller).data, status=201)



class ResellerListView(generics.ListAPIView):
    queryset           = Reseller.objects.select_related('user').order_by('-created_at')
    serializer_class   = ResellerSerializer
    permission_classes = [IsAuthenticated]



class ResellerLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.contrib.auth import authenticate

        username = request.data.get('username')
        password = request.data.get('password')
        user     = authenticate(username=username, password=password)

        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        try:
            reseller = Reseller.objects.get(user=user)
        except Reseller.DoesNotExist:
            return Response({"error": "Not a reseller account"}, status=403)

        if not reseller.is_active:
            return Response({"error": "Account suspended. Contact admin."}, status=403)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access":        str(refresh.access_token),
            "refresh":       str(refresh),
            "reseller_id":   reseller.id,
            "business_name": reseller.business_name,
            "balance":       str(reseller.balance),
        })


class ResellerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            reseller = Reseller.objects.get(user=request.user)
        except Reseller.DoesNotExist:
            return Response({"error": "Not a reseller"}, status=403)
        return Response(ResellerSerializer(reseller).data)



class ResellerTopUpView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            reseller = Reseller.objects.get(user=request.user)
        except Reseller.DoesNotExist:
            return Response({"error": "Not a reseller"}, status=403)

        phone  = request.data.get('phone', '').strip()
        amount = request.data.get('amount')

        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]

        topup  = ResellerTopUp.objects.create(reseller=reseller, amount=amount)
        result = stk_push(phone, amount, f"topup-{reseller.id}")

        if result.get('ResponseCode') == '0':
            topup.checkout_req_id = result['CheckoutRequestID']
            topup.save()
            return Response({"topup_id": topup.id, "message": "STK push sent"})
        else:
            topup.delete()
            return Response({"error": result.get('errorMessage', 'STK push failed')}, status=400)


# M-Pesa callback for reseller 
class ResellerTopUpCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        body        = request.data.get('Body', {}).get('stkCallback', {})
        result_code = body.get('ResultCode')
        checkout_id = body.get('CheckoutRequestID')

        try:
            topup    = ResellerTopUp.objects.get(checkout_req_id=checkout_id)
            reseller = topup.reseller
        except ResellerTopUp.DoesNotExist:
            return Response({"ResultCode": 0, "ResultDesc": "Accepted"})

        if result_code == 0:
            items      = body.get('CallbackMetadata', {}).get('Item', [])
            mpesa_code = next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), '')
            topup.mpesa_code = mpesa_code
            topup.paid_at    = timezone.now()
            topup.save()
            # Credit reseller balance
            reseller.balance += topup.amount
            reseller.save()

        return Response({"ResultCode": 0, "ResultDesc": "Accepted"})


# Reseller buys a batch of vouchers
class ResellerBuyVouchersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            reseller = Reseller.objects.get(user=request.user)
        except Reseller.DoesNotExist:
            return Response({"error": "Not a reseller"}, status=403)

        package_id = request.data.get('package_id')
        quantity   = int(request.data.get('quantity', 0))

        try:
            package = Package.objects.get(id=package_id, is_active=True)
        except Package.DoesNotExist:
            return Response({"error": "Package not found"}, status=404)

        # Reseller gets 20% discount — adjust as needed
        unit_price = package.price_ksh * 0.80
        total_cost = unit_price * quantity

        if reseller.balance < total_cost:
            return Response({
                "error": f"Insufficient balance. You need KES {total_cost} but have KES {reseller.balance}"
            }, status=400)

        # Deduct balance
        reseller.balance -= total_cost
        reseller.save()

        # Generate voucher codes
        batch = ResellerVoucherBatch.objects.create(
            reseller   = reseller,
            package    = package,
            quantity   = quantity,
            unit_price = unit_price,
            total_cost = total_cost,
        )

        vouchers = []
        for _ in range(quantity):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            # make sure code is unique
            while Voucher.objects.filter(code=code).exists():
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            v = Voucher.objects.create(package=package, code=code)
            vouchers.append(v.code)

        return Response({
            "batch_id":   batch.id,
            "quantity":   quantity,
            "unit_price": unit_price,
            "total_cost": total_cost,
            "balance_left": str(reseller.balance),
            "vouchers":   vouchers,
        })


# Reseller views their vouchers
class ResellerVouchersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            reseller = Reseller.objects.get(user=request.user)
        except Reseller.DoesNotExist:
            return Response({"error": "Not a reseller"}, status=403)

        batches = ResellerVoucherBatch.objects.filter(reseller=reseller).order_by('-created_at')
        return Response(ResellerVoucherBatchSerializer(batches, many=True).data)


# Reseller top up history
class ResellerTopUpHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            reseller = Reseller.objects.get(user=request.user)
        except Reseller.DoesNotExist:
            return Response({"error": "Not a reseller"}, status=403)

        topups = ResellerTopUp.objects.filter(reseller=reseller).order_by('-created_at')
        return Response(ResellerTopUpSerializer(topups, many=True).data)