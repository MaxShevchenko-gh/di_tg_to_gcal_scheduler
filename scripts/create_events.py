"""
One-shot: create Google Calendar events for all attended future events.
Safe to re-run — already-processed events are skipped via the state DB.

    python scripts/create_events.py
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
CAL_ID   = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
LIMIT    = int(os.getenv('SCAN_LIMIT', '300'))

from calendar_client import CalendarClient
from event_parser import is_event_poll, user_is_attending, parse_event_message
from state import StateDB


async def main():
    db       = StateDB(DATA_DIR)
    calendar = CalendarClient(DATA_DIR, CAL_ID)

    session_path = os.path.join(DATA_DIR, 'telegram_session')
    api_id   = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']

    async with TelegramClient(session_path, api_id, api_hash) as client:
        print(f'Scanning @{CHANNEL} for events @{USERNAME} is attending…\n')

        created = skipped_past = skipped_done = 0

        async for msg in client.iter_messages(CHANNEL, limit=LIMIT):
            if not msg.message:
                continue
            if not is_event_poll(msg.message) or not user_is_attending(msg.message, USERNAME):
                continue

            event = parse_event_message(msg.message, TIMEZONE)

            if event.start_dt and event.start_dt < datetime.now(timezone.utc):
                print(f'SKIP past     "{event.title}"  ({event.start_dt})')
                skipped_past += 1
                continue

            if db.is_processed(msg.id):
                print(f'SKIP already  "{event.title}"')
                skipped_done += 1
                continue

            try:
                source_url = f'https://t.me/{CHANNEL}/{msg.id}'
                cal_id = calendar.create_event(event, timezone=TIMEZONE, source_url=source_url)
                db.mark_processed(msg.id, CHANNEL, cal_id)
                print(f'CREATED       "{event.title}"  {event.start_dt}')
                created += 1
            except Exception as exc:
                print(f'ERROR         "{event.title}": {exc}')

        print(f'\nDone. Created: {created}  |  Skipped past: {skipped_past}  |  Already existed: {skipped_done}')


asyncio.run(main())
