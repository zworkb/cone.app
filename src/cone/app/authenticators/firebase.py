import json

import requests

from zope.interface import implementer
from node.ext.ugm.interfaces import IAuthenticator

REST_API_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"


def sign_in_with_email_and_password(email: str, password: str, api_key, return_secure_token: bool = True):
    """
    https://github.com/billydh/python-firebase-admin-sdk-demo/blob/master/sign_in_with_email_and_password.py
    """

    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": return_secure_token
    })

    r = requests.post(REST_API_URL,
                      params={"key": api_key},
                      data=payload)

    return r.json()

@implementer(IAuthenticator)
class FirebaseAuthenticator:
    def __init__(self, users, api_key):
        self.users = users
        self.api_key = api_key

    def authenticate(self, uid, pwd):
        """
        does firebase authentication and in the case of success
        checks if the uid exists in self.users, if not it creates the user there
        when fb login is unsuccessful delegates it to
        """
        res = sign_in_with_email_and_password(uid, pwd, self.api_key)

        if res.get("kind") == 'identitytoolkit#VerifyPasswordResponse':
            id = res["localId"]
            users = self.users
            if id not in users:
                users.create(
                    id,
                    login="email",
                    email=res["email"],
                    fullname=res["displayName"],
                    registered=res["registered"],
                    idtoken=res["idToken"]
                )

            user = users[id]
            if hasattr(users, "on_authenticated"):
                users.on_authenticated(res["localId"])
            # user.passwd(None, pwd)  # it is to decide if we need local pwds
            return res
        else:
            # if not found in firebase login locally
            return self.users.authenticate(uid, pwd)