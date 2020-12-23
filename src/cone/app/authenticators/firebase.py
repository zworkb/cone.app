import json

import requests

# TODO: key is hardcoded now, must be fetched from config
FIREBASE_WEB_API_KEY = "AIzaSyDqQThSScLrwBybYW5m22rZSYILELPsDz8"
rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


def sign_in_with_email_and_password(email: str, password: str, return_secure_token: bool = True):
    """
    https://github.com/billydh/python-firebase-admin-sdk-demo/blob/master/sign_in_with_email_and_password.py
    """

    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": return_secure_token
    })

    r = requests.post(rest_api_url,
                      params={"key": FIREBASE_WEB_API_KEY},
                      data=payload)

    return r.json()
