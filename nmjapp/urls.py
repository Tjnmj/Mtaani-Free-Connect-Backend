from django.urls import path
from .views import (
    CreateUserView,
    PackageListView,
    InitiatePaymentView,
    MpesaCallbackView,
    SessionStatusView,
    ActivateVoucherView,
    ReconnectView,
    DashboardStatsView,   
    RouterListView,        
    HotspotUserListView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('register/',         CreateUserView.as_view(),       name='register'),
    path('login/',            TokenObtainPairView.as_view(),  name='login'),
    path('token/refresh/',    TokenRefreshView.as_view(),     name='refresh'),
    path('packages/',         PackageListView.as_view(),      name='packages'),
    path('pay/',              InitiatePaymentView.as_view(),  name='pay'),
    path('mpesa/callback/',   MpesaCallbackView.as_view(),    name='mpesa-callback'),
   path('session/<int:pk>/',   SessionStatusView.as_view(), name='session-status'),
    path('voucher/activate/',    ActivateVoucherView.as_view(),  name='voucher-activate'),
    path('reconnect/',        ReconnectView.as_view(),        name='reconnect'),
    path('dashboard/stats/',  DashboardStatsView.as_view(),   name='dashboard-stats'),
    path('routers/',          RouterListView.as_view(),        name='routers'),
    path('hotspot/users/',    HotspotUserListView.as_view(),   name='hotspot-users'),
]