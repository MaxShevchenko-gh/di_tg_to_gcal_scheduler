# DomIgri TG → Google Calendar Scheduler

Monitors the [t.me/domigri](https://t.me/domigri) Telegram channel for event polls you voted to attend, and automatically creates Google Calendar events with a 1-hour reminder.

## How it works

The domigri channel posts game-night events as bot-managed polls with two options:

- **Я прийду** (I'll attend)
- **Місць немає я запасний** (Waitlist)

When you click "Я прийду", the bot adds your `@username` to the message. This tool scans for messages where your username appears in the attending section, parses the event title and date from the first line, and creates a Google Calendar event.

It runs daily as a **GitHub Actions** scheduled workflow — no server required.

## Setup

See [SETUP.md](SETUP.md) for the full step-by-step guide covering:

1. Telegram API credentials
2. Google Cloud OAuth setup
3. One-time authentication (Telegram session + Google token)
4. GitHub Actions secrets configuration

## Secrets required

| Secret | Description |
|---|---|
| `TELEGRAM_API_ID` | From [my.telegram.org/apps](https://my.telegram.org/apps) |
| `TELEGRAM_API_HASH` | From [my.telegram.org/apps](https://my.telegram.org/apps) |
| `TELEGRAM_USERNAME` | Your Telegram username (without @) |
| `TELEGRAM_SESSION_B64` | Base64-encoded Telethon session file |
| `GOOGLE_TOKEN_B64` | Base64-encoded Google OAuth token |
| `GOOGLE_CREDS_B64` | Base64-encoded Google OAuth credentials |

## Local scripts

| Script | Purpose |
|---|---|
| `scripts/auth_telegram.py` | One-time Telegram authentication |
| `scripts/auth_google.py` | One-time Google Calendar authentication |
| `scripts/dry_run.py` | Preview events that would be created (no writes) |
| `scripts/run_scan.py` | Run a full scan and create events |
| `scripts/inspect_messages.py` | Dump raw channel messages for debugging |

## Schedule

Runs daily at **10:00 Kyiv time** (07:00 UTC). Can also be triggered manually from the GitHub Actions tab.
