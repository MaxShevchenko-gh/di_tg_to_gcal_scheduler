import logging
import os
from datetime import timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from event_parser import EventInfo

logger = logging.getLogger(__name__)

_SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarClient:
    def __init__(self, data_dir: str, calendar_id: str = 'primary'):
        self._calendar_id = calendar_id
        self._token_path = os.path.join(data_dir, 'token.json')
        self._service = self._build_service()

    def _build_service(self):
        creds = Credentials.from_authorized_user_file(self._token_path, _SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(self._token_path, 'w') as f:
                f.write(creds.to_json())
        return build('calendar', 'v3', credentials=creds)

    def event_exists(self, msg_id: int) -> bool:
        """Return True if a calendar event was already created for this Telegram message ID."""
        result = self._service.events().list(
            calendarId=self._calendar_id,
            privateExtendedProperty=f'tg_msg_id={msg_id}',
            showDeleted=False,
        ).execute()
        return bool(result.get('items'))

    def create_event(self, event: EventInfo, timezone: str, msg_id: int, source_url: str | None = None) -> str:
        start = event.start_dt
        end = start + timedelta(hours=2)

        body: dict = {
            'summary': event.title,
            'description': event.description,
            'start': {'dateTime': start.isoformat(), 'timeZone': timezone},
            'end':   {'dateTime': end.isoformat(),   'timeZone': timezone},
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},
                ],
            },
            'extendedProperties': {
                'private': {'tg_msg_id': str(msg_id)},
            },
        }

        if source_url:
            body['source'] = {'title': 'Telegram (domigri)', 'url': source_url}

        result = self._service.events().insert(
            calendarId=self._calendar_id,
            body=body,
        ).execute()

        event_id: str = result['id']
        logger.info('Calendar event created: %s  link=%s', event_id, result.get('htmlLink'))
        return event_id
