# adm/ad_client.py
import requests
from django.conf import settings

class AdClient:
    BASE_URL = "http://10.8.27.97:8056/api/active-directory/1.0.12"

    @classmethod
    def get_refresh_token(cls, email: str, password: str):
        url = f"{cls.BASE_URL}/account/{email}/authorization"
        print(email + password)
        try:
            response = requests.post(url, json={"password": password}, timeout=10)
            response.raise_for_status()
            print(response.json())
            return response.json()  # { "token": "...", "expiresIn": ... }
        except requests.exceptions.RequestException as e:
            raise Exception(f"AD authorization error: {str(e)}")
