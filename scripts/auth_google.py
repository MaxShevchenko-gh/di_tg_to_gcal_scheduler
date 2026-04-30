"""
Run once on the host (NOT inside Docker) to authorise Google Calendar access.

Prerequisites:
  1. Download OAuth credentials from Google Cloud Console (see SETUP.md step 3)
     and save the file as:  data/credentials.json
  2. Then run:
        pip install google-auth-oauthlib python-dotenv
        python scripts/auth_google.py

A browser window will open asking you to sign in and grant calendar access.
The resulting token is saved to data/token.json and is used by the Docker
container on every subsequent start — re-auth only needed if the token expires
or is revoked (refresh tokens are long-lived).
"""
import os
import sys

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

# Always use the local ./data folder — DATA_DIR=/data in .env is for Docker only
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

SCOPES          = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_PATH = os.path.join(DATA_DIR, 'credentials.json')
TOKEN_PATH       = os.path.join(DATA_DIR, 'token.json')

if not os.path.exists(CREDENTIALS_PATH):
    print(f'ERROR: {CREDENTIALS_PATH} not found.')
    print('Download it from Google Cloud Console → APIs & Services → Credentials')
    print('and save it as data/credentials.json')
    sys.exit(1)

flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
creds = flow.run_local_server(port=0)

with open(TOKEN_PATH, 'w') as f:
    f.write(creds.to_json())

print('\nGoogle Calendar authorisation successful!')
print('Token saved to:', TOKEN_PATH)
print('You can now start the Docker container.')
