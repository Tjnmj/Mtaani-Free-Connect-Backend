import base64
import requests
from datetime import datetime
from django.conf import settings


def get_access_token():
    credentials = f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}"
    encoded     = base64.b64encode(credentials.encode()).decode()

    url = (
        "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        if settings.MPESA_ENV == 'sandbox'
        else "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    )

    r = requests.get(url, headers={"Authorization": f"Basic {encoded}"})
    return r.json()['access_token']


def stk_push(phone: str, amount: int, session_id: str) -> dict:
    token     = get_access_token()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    raw_password = f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    password     = base64.b64encode(raw_password.encode()).decode()

    base_url = (
        "https://sandbox.safaricom.co.ke"
        if settings.MPESA_ENV == 'sandbox'
        else "https://api.safaricom.co.ke"
    )

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            amount,
        "PartyA":            phone,
        "PartyB":            settings.MPESA_SHORTCODE,
        "PhoneNumber":       phone,
        "CallBackURL":       settings.MPESA_CALLBACK_URL,
        "AccountReference":  session_id,
        "TransactionDesc":   "WiFi Access",
    }

    r = requests.post(
        f"{base_url}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.json()