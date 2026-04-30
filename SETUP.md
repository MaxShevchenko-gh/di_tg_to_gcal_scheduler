# Setup Guide

## Prerequisites

- Docker Desktop installed and running on Windows
- Python 3.12+ installed on the host (for one-time auth scripts only)
- A Telegram account subscribed to t.me/domigri
- A Google account

---

## Step 1 — Telegram API credentials

1. Go to https://my.telegram.org/apps and log in with your phone number.
2. Create a new application (name/description can be anything, e.g. "tg-scheduler").
3. Copy the **App api_id** and **App api_hash** values.

---

## Step 2 — Configure environment

```
cp .env.example .env
```

Open `.env` and fill in:

```
TELEGRAM_API_ID=<your api_id>
TELEGRAM_API_HASH=<your api_hash>
TELEGRAM_PHONE=<your phone in international format, e.g. +380671234567>
```

The other values can stay at their defaults for now.

---

## Step 3 — Google Cloud OAuth credentials

1. Go to https://console.cloud.google.com/
2. Create a new project (or select an existing one), e.g. **tg-scheduler**.
3. Enable the **Google Calendar API**:
   - In the left menu: *APIs & Services → Library*
   - Search "Google Calendar API" → click it → **Enable**
4. Create OAuth credentials:
   - *APIs & Services → Credentials → Create Credentials → OAuth client ID*
   - Application type: **Desktop app**
   - Name: anything (e.g. "tg-scheduler")
   - Click **Create**
5. Click **Download JSON** on the credentials that just appeared.
6. Save the downloaded file as `data/credentials.json` in this project.
7. Configure the OAuth consent screen (required even for personal use):
   - *APIs & Services → OAuth consent screen*
   - User type: **External** → Create
   - Fill in App name (e.g. "tg-scheduler"), your email for support & developer contact
   - Scopes: click *Add or Remove Scopes* → add `https://www.googleapis.com/auth/calendar`
   - Test users: add your own Google email address
   - Save and continue through all steps

---

## Step 4 — One-time authentication

Install the auth dependencies on your host machine:

```
pip install telethon google-auth-oauthlib python-dotenv
```

### Authenticate with Telegram

```
python scripts/auth_telegram.py
```

- Enter your phone number when prompted.
- Enter the code Telegram sends you.
- Session is saved to `data/telegram_session.session`.

### Authenticate with Google Calendar

```
python scripts/auth_google.py
```

- A browser window opens — sign in with your Google account.
- Grant calendar access when asked.
- Token is saved to `data/token.json`.

---

## Step 5 — Build and start the Docker container

```
docker compose up -d --build
```

The container will:
- Start automatically whenever Docker Desktop starts.
- Run `restart: always`, so it restarts after crashes or reboots.
- On first start, scan your last 300 messages in domigri for polls you already voted on and create calendar events for them.
- From then on, create new calendar events in real-time when you vote, and re-scan every 30 minutes as a safety net.

### Check logs

```
docker compose logs -f
```

### Stop

```
docker compose down
```

---

## Docker Desktop auto-start on Windows boot

Open Docker Desktop → Settings → General → enable **"Start Docker Desktop when you sign in to your computer"**.

The container's `restart: always` policy ensures it comes back up automatically each time Docker starts.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `TELEGRAM_API_ID missing` | Check your `.env` file |
| `token.json not found` | Re-run `scripts/auth_google.py` |
| `telegram_session.session not found` | Re-run `scripts/auth_telegram.py` |
| Calendar events created with wrong time | Set `EVENT_TIMEZONE` in `.env` |
| Poll date not parsed correctly | The channel uses an unusual format — open an issue |
