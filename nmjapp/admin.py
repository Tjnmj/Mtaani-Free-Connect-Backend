from django.contrib import admin
from .models import Package,Payment,Reconnect,Voucher,Session

admin.site.register(Package)
admin.site.register(Payment)
admin.site.register(Session)
admin.site.register(Voucher)
admin.site.register(Reconnect)
