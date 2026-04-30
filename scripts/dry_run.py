"""
Dry run: scan the channel for events you're attending and print what calendar
events would be created, without writing anything to Google Calendar.

    python scripts/dry_run.py
    python scripts/dry_run.py 100   # scan last 100 messages (default 300)
"""
import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CHANNEL  = os.getenv('TELEGRAM_CHANNEL', 'domigri')
USERNAME = os.getenv('TELEGRAM_USERNAME', '')
TIMEZONE = os.getenv('EVENT_TIMEZONE', 'Europe/Kyiv')
LIMIT    = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv('SCAN_LIMIT', '300'))

from event_parser import is_event_poll, user_is_attending, parse_event_message


async def main():
    if not USERNAME:
        print('ERROR: TELEGRAM_USERNAME is not set in .env')
        sys.exit(1)

    session_path = os.path.join(DATA_DIR, 'telegram_session')
    api_id   = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']

    async with TelegramClient(session_path, api_id, api_hash) as client:
        print(f'Scanning last {LIMIT} messages in @{CHANNEL} for events @{USERNAME} is attending…\n')

        found = 0
        async for msg in client.iter_messages(CHANNEL, limit=LIMIT):
            if not msg.message:
                continue
            if not is_event_poll(msg.message):
                continue
            if not user_is_attending(msg.message, USERNAME):
                continue

            event = parse_event_message(msg.message, TIMEZONE)

            if event.start_dt and event.start_dt < datetime.now(timezone.utc):
                print(f'SKIP (past)  msg {msg.id}  "{event.title}"  {event.start_dt}')
                continue

            found += 1
            print(f'{"─" * 60}')
            print(f'Msg ID    : {msg.id}')
            print(f'Title     : {event.title}')
            print(f'Date/Time : {event.start_dt}')
            print(f'URL       : https://t.me/{CHANNEL}/{msg.id}')
            print(f'Raw first line: {msg.message.splitlines()[0]}')
            print()

        if found == 0:
            print(f'No attended events found for @{USERNAME} in the last {LIMIT} messages.')
        else:
            print(f'{"─" * 60}')
            print(f'Total: {found} event(s) found.')
            print()
            print('If the parsed dates/titles look correct, run:')
            print('  docker compose up -d --build')


asyncio.run(main())
