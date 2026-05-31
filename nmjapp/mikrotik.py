import routeros_api
import os
from django.conf import settings

MIKROTIK_HOST           = settings.MIKROTIK_HOST
MIKROTIK_USER           = settings.MIKROTIK_USER
MIKROTIK_PASSWORD       = settings.MIKROTIK_PASSWORD
MIKROTIK_HOTSPOT_SERVER = settings.MIKROTIK_HOTSPOT_SERVER
MIKROTIK_PPPOE_SERVER   = settings.MIKROTIK_PPPOE_SERVER



def get_connection():
    """Open a connection to the MikroTik router."""
    connection = routeros_api.RouterOsApiPool(
        MIKROTIK_HOST,
        username=MIKROTIK_USER,
        password=MIKROTIK_PASSWORD,
        plaintext_login=True
    )
    return connection.get_api()

# HOTSPOT 
def hotspot_add_user(username, password, profile, comment=""):
    """
    Add a hotspot user on MikroTik.
    Called when a session becomes active.
    profile = package name (must match a hotspot user profile on router)
    """
    try:
        api = get_connection()
        api.get_resource('/ip/hotspot/user').add(
            name=username,
            password=password,
            profile=profile,
            comment=comment,
            server=MIKROTIK_HOTSPOT_SERVER,
        )
        return True
    except Exception as e:
        print(f"[MikroTik] hotspot_add_user error: {e}")
        return False


def hotspot_remove_user(username):
    """
    Remove a hotspot user from MikroTik.
    Called when session expires or is cancelled.
    """
    try:
        api = get_connection()
        resource = api.get_resource('/ip/hotspot/user')
        users = resource.get(name=username)
        for user in users:
            resource.remove(id=user['id'])
        return True
    except Exception as e:
        print(f"[MikroTik] hotspot_remove_user error: {e}")
        return False


def hotspot_kick_active_user(username):
    """
    Kick an actively connected hotspot user.
    Called when session expires mid-use.
    """
    try:
        api = get_connection()
        resource = api.get_resource('/ip/hotspot/active')
        active = resource.get(user=username)
        for session in active:
            resource.remove(id=session['id'])
        return True
    except Exception as e:
        print(f"[MikroTik] hotspot_kick_active_user error: {e}")
        return False

# PPPOE 
def pppoe_add_secret(username, password, profile, service="pppoe", comment=""):
    """
    Add a PPPoE secret (account) on MikroTik.
    Called when a PPPoE client is created or renewed.
    profile = PPPoE plan name (must match a PPP profile on router)
    """
    try:
        api = get_connection()
        api.get_resource('/ppp/secret').add(
            name=username,
            password=password,
            service=service,
            profile=profile,
            comment=comment,
        )
        return True
    except Exception as e:
        print(f"[MikroTik] pppoe_add_secret error: {e}")
        return False


def pppoe_update_secret(username, password=None, profile=None):
    """
    Update an existing PPPoE secret.
    Called when a client renews — update profile/password if changed.
    """
    try:
        api = get_connection()
        resource = api.get_resource('/ppp/secret')
        secrets  = resource.get(name=username)
        for secret in secrets:
            update = {}
            if password: update['password'] = password
            if profile:  update['profile']  = profile
            resource.set(id=secret['id'], **update)
        return True
    except Exception as e:
        print(f"[MikroTik] pppoe_update_secret error: {e}")
        return False


def pppoe_remove_secret(username):
    """
    Remove a PPPoE secret from MikroTik.
    Called when a client is deleted or suspended.
    """
    try:
        api = get_connection()
        resource = api.get_resource('/ppp/secret')
        secrets  = resource.get(name=username)
        for secret in secrets:
            resource.remove(id=secret['id'])
        return True
    except Exception as e:
        print(f"[MikroTik] pppoe_remove_secret error: {e}")
        return False


def pppoe_disconnect_active(username):
    """
    Disconnect an active PPPoE session.
    Called when client expires mid-session.
    """
    try:
        api = get_connection()
        resource = api.get_resource('/ppp/active')
        active   = resource.get(name=username)
        for session in active:
            resource.remove(id=session['id'])
        return True
    except Exception as e:
        print(f"[MikroTik] pppoe_disconnect_active error: {e}")
        return False


def pppoe_enable_secret(username):
    """Re-enable a disabled PPPoE secret."""
    try:
        api = get_connection()
        resource = api.get_resource('/ppp/secret')
        secrets  = resource.get(name=username)
        for secret in secrets:
            resource.set(id=secret['id'], disabled='false')
        return True
    except Exception as e:
        print(f"[MikroTik] pppoe_enable_secret error: {e}")
        return False


def pppoe_disable_secret(username):
    """
    Disable a PPPoE secret without deleting it.
    Called when client expires — blocks login without losing the account.
    """
    try:
        api = get_connection()
        resource = api.get_resource('/ppp/secret')
        secrets  = resource.get(name=username)
        for secret in secrets:
            resource.set(id=secret['id'], disabled='true')
        return True
    except Exception as e:
        print(f"[MikroTik] pppoe_disable_secret error: {e}")
        return False

# ROUTER STATUS
def check_router_online():
    """
    Check if the router is reachable.
    Used by your router status dashboard stat.
    """
    try:
        api = get_connection()
        api.get_resource('/system/identity').get()
        return True
    except Exception:
        return False