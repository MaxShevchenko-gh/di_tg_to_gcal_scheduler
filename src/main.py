import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from calendar_client import CalendarClient
from event_parser import parse_event_message
from state import StateDB
from telegram_client import TGClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(name)s  %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _cfg(key: str, default: str | None = None) -> str:
    val = os.getenv(key, default)
    if val is None:
        raise RuntimeError(f'Missing required env variable: {key}')
    return val


DATA_DIR      = _cfg('DATA_DIR', './data')
CHANNEL       = _cfg('TELEGRAM_CHANNEL', 'domigri')
USERNAME      = _cfg('TELEGRAM_USERNAME')
CALENDAR_ID   = _cfg('GOOGLE_CALENDAR_ID', 'primary')
TIMEZONE      = _cfg('EVENT_TIMEZONE', 'Europe/Kyiv')
SCAN_INTERVAL = int(_cfg('SCAN_INTERVAL_MINUTES', '30')) * 60
SCAN_LIMIT    = int(_cfg('SCAN_LIMIT', '300'))


async def _process(msg, db: StateDB, calendar: CalendarClient):
    if db.is_processed(msg.id):
        return

    event = parse_event_message(msg.message, TIMEZONE)

    if event.start_dt and event.start_dt < datetime.now(timezone.utc):
        logger.info('Skipping past event msg %s "%s" (%s)', msg.id, event.title, event.start_dt)
        db.mark_processed(msg.id, CHANNEL)
        return

    logger.info('Processing msg %s → "%s" on %s', msg.id, event.title, event.start_dt)

    try:
        source_url = f'https://t.me/{CHANNEL}/{msg.id}'
        cal_id = calendar.create_event(event, timezone=TIMEZONE, source_url=source_url)
        db.mark_processed(msg.id, CHANNEL, cal_id)
    except Exception as exc:
        logger.error('Calendar write failed for msg %s: %s', msg.id, exc)


async def _scan(tg: TGClient, db: StateDB, calendar: CalendarClient):
    logger.info('Starting channel scan (limit=%d)…', SCAN_LIMIT)
    try:
        attended = await tg.get_attended_events(limit=SCAN_LIMIT)
        for msg in attended:
            await _process(msg, db, calendar)
    except Exception as exc:
        logger.error('Scan error: %s', exc)


async def main():
    db = StateDB(DATA_DIR)
    calendar = CalendarClient(DATA_DIR, CALENDAR_ID)

    tg = TGClient(
        data_dir=DATA_DIR,
        api_id=int(_cfg('TELEGRAM_API_ID')),
        api_hash=_cfg('TELEGRAM_API_HASH'),
        channel=CHANNEL,
        username=USERNAME,
    )

    await tg.start()

    # Real-time: fires when the bot edits the message after you click the button
    tg.on_vote(lambda msg: _process(msg, db, calendar))

    # Startup scan for events already voted on
    await _scan(tg, db, calendar)

    # Periodic re-scan as safety net
    async def _periodic():
        while True:
            await asyncio.sleep(SCAN_INTERVAL)
            await _scan(tg, db, calendar)

    logger.info('Scheduler running. Scan interval: %d min', SCAN_INTERVAL // 60)
    await asyncio.gather(tg.run(), _periodic())


if __name__ == '__main__':
    asyncio.run(main())
