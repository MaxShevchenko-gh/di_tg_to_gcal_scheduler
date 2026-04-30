"""
Run once on the host (NOT inside Docker) to create the Telethon session file.

    pip install telethon python-dotenv
    python scripts/auth_telegram.py

It will prompt for your phone number and the verification code sent by Telegram.
The session is saved to data/telegram_session.session and is reused by the
Docker container on every subsequent start — you won't need to re-authenticate.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from telethon.sync import TelegramClient

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

api_id   = int(os.environ['TELEGRAM_API_ID'])
api_hash = os.environ['TELEGRAM_API_HASH']
phone    = os.environ['TELEGRAM_PHONE']

session_path = os.path.join(DATA_DIR, 'telegram_session')

with TelegramClient(session_path, api_id, api_hash) as client:
    client.start(phone=phone)
    me = client.get_me()
    print(f'\nAuthenticated as: {me.first_name} (@{me.username})')
    print('Session saved to:', session_path + '.session')
    print('You can now start the Docker container.')
