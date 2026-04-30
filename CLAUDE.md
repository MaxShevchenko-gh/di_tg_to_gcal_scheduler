# TG Scheduler

Monitors a Telegram channel (t.me/domigri) for event polls the user voted on,
and automatically creates Google Calendar events with reminders.

## Architecture

```
src/main.py           — orchestration: startup scan + real-time listener + periodic re-scan
src/telegram_client.py — Telethon user-account client; detects voted polls via chosen=True
src/event_parser.py   — extracts title/date/time/location from poll question text (RU/UA)
src/calendar_client.py — Google Calendar API wrapper; creates events with popup reminders
src/state.py          — SQLite dedup: tracks which poll message IDs were already processed
```

Data written to `./data/` (mounted as Docker volume, gitignored):
- `telegram_session.session` — Telethon auth session
- `token.json`               — Google OAuth token
- `credentials.json`         — Google OAuth client credentials
- `state.db`                 — processed poll IDs

## One-time setup

See SETUP.md for the full guided walkthrough.

## Running

```bash
docker compose up -d --build   # start
docker compose logs -f         # watch logs
docker compose down            # stop
```

Auth scripts (host only, not in Docker):
```bash
python scripts/auth_telegram.py
python scripts/auth_google.py
```

## Key env vars

| Variable | Default | Purpose |
|---|---|---|
| TELEGRAM_CHANNEL | domigri | Channel username to watch |
| GOOGLE_CALENDAR_ID | primary | Target calendar |
| EVENT_TIMEZONE | Europe/Kyiv | Timezone for created events |
| SCAN_INTERVAL_MINUTES | 30 | Periodic re-scan cadence |
| SCAN_LIMIT | 300 | Messages to fetch per scan |
