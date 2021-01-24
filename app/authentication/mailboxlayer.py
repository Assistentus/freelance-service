import requests
from django.conf import settings


def validate_email(email: str) -> bool:
    request = requests.get(f'http://apilayer.net/api/check?access_key={settings.MAILBOXLAYER_API_KEY}&email={email}')
    data = request.json()

    if data['smtp_check'] and data['mx_found']:
        return True
    else:
        return False