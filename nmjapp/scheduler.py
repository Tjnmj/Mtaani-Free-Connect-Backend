from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from .models import Session, PPPoEClient
from .mikrotik import (
    hotspot_kick_active_user, hotspot_remove_user,
    pppoe_disable_secret, pppoe_disconnect_active
)

def expire_hotspot_sessions():
    """Find expired hotspot sessions and kick them off MikroTik."""
    expired = Session.objects.filter(
        status='active',
        expires_at__lt=timezone.now()
    )
    for session in expired:
        hotspot_kick_active_user(session.phone)
        hotspot_remove_user(session.phone)
        session.status = 'expired'
        session.save()
        print(f"[SCHEDULER] Expired hotspot session: {session.phone}")


def expire_pppoe_clients():
    """Find expired PPPoE clients and disable them on MikroTik."""
    expired = PPPoEClient.objects.filter(
        status='active',
        expires_at__lt=timezone.now()
    )
    for client in expired:
        pppoe_disconnect_active(client.username)
        pppoe_disable_secret(client.username)
        client.status = 'expired'
        client.save()
        print(f"[SCHEDULER] Expired PPPoE client: {client.username}")


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        expire_hotspot_sessions,
        'interval',
        minutes=5,
        id='expire_hotspot_sessions',
        replace_existing=True,
    )
    scheduler.add_job(
        expire_pppoe_clients,
        'interval',
        minutes=5,
        id='expire_pppoe_clients',
        replace_existing=True,
    )

    scheduler.start()
    print("[SCHEDULER] Started successfully.")