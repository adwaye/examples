# noqa D100
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
TOKEN_PATH = str(Path(FILE_PATH, "token.json"))
CREDENTIALS_PATH = str(Path(FILE_PATH, "credentials_adwaye_compose.json"))


def authenticate():
    """Authenticate function.

    Returns
    -------
    _type_
        _description_
    """
    print("\n=============== Authenticating for Gmail: start ===============")
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # fmt: off
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
            # fmt: on
        # Save the credentials for the next run
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    print("\n=============== Authenticating for Gmail: end ===============")
    return creds
