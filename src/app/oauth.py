from google_auth_oauthlib.flow import InstalledAppFlow
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi.responses import RedirectResponse, HTMLResponse
from google.auth.transport.requests import Request
import os.path

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/userinfo.email", "openid"]
OAUTH_REDIRECT_URI = "http://localhost:8080/oauth2/callback"

from fastapi import FastAPI

oauth2Api = FastAPI()


def is_user_logged_in(email: str):
    authorized_user_file = f"user-credentials/{email}.json"
    if not os.path.exists(authorized_user_file):
        return False
    try:
        creds = Credentials.from_authorized_user_file(authorized_user_file, SCOPES)
    except:
        return False
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(authorized_user_file, 'w') as f:
                f.write(creds.to_json())
            return True
        except:
            return False
    return creds.valid


def get_user_credentials(email: str):
    authorized_user_file = f"user-credentials/{email}.json"
    credentials = Credentials.from_authorized_user_file(authorized_user_file, SCOPES)
    return credentials


def generate_authorization_url(email: str):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('credentials.json',
                                                                   scopes=SCOPES)
    flow.redirect_uri = OAUTH_REDIRECT_URI
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        login_hint=email,
        prompt='consent')
    return authorization_url


def exchange_credentials_from_authorization_code(code: str, state: str):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('credentials.json',
                                                                   scopes=SCOPES, state=state)
    flow.redirect_uri = OAUTH_REDIRECT_URI
    flow.fetch_token(code=code)
    return flow.credentials


def token_introspection(credentials):
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    return {
        "email": user_info.get('email'),
    }


@oauth2Api.get("/callback")
def handle_oauth2_callback(error: str | None = None, code: str | None = None, state: str | None = None):
    if error is not None:
        return RedirectResponse(f"/oauth2/error?error={error}")
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('credentials.json',
                                                                   scopes=SCOPES, state=state)
    flow.redirect_uri = OAUTH_REDIRECT_URI
    flow.fetch_token(code=code)
    credentials = flow.credentials

    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    user_email = user_info.get('email')

    with open(f"user-credentials/{user_email}.json", 'w') as f:
        f.write(credentials.to_json())
    return RedirectResponse(f"/oauth2/success")


@oauth2Api.get("/error")
def handle_oauth2_error(error: str):
    return HTMLResponse(f"""<html><body>Error: ${error}</body></html>""")


@oauth2Api.get("/success")
def handle_oauth2_success():
    return HTMLResponse("""<html><body>Login Success!</body></html>""")


class LoginRequiredException(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"""Login is required!
Open {generate_authorization_url(email)} to login.""")
