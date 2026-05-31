from django.contrib import admin
from .models import FreeTrial, IPPool, PPPoEClient, PPPoEPlan,PPPoEPayment, Package,Payment,Reconnect,Voucher,Session,Router

admin.site.register(Package)
admin.site.register(Payment)
admin.site.register(Session)
admin.site.register(Voucher)
admin.site.register(Reconnect)
admin.site.register(Router)
admin.site.register(FreeTrial)
admin.site.register(IPPool)
admin.site.register(PPPoEPlan)
admin.site.register(PPPoEClient)
admin.site.register(PPPoEPayment)
