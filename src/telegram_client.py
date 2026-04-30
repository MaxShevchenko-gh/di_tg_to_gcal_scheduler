import logging
import os
from collections.abc import Awaitable, Callable

from telethon import TelegramClient, events
from telethon.tl.types import Message

from event_parser import is_event_poll, user_is_attending

logger = logging.getLogger(__name__)

VoteCallback = Callable[[Message], Awaitable[None]]


class TGClient:
    def __init__(self, data_dir: str, api_id: int, api_hash: str, channel: str, username: str):
        session_path = os.path.join(data_dir, 'telegram_session')
        self._client  = TelegramClient(session_path, api_id, api_hash)
        self._channel = channel
        self._username = username

    async def start(self):
        await self._client.start()
        logger.info('Telethon client connected')

    async def get_attended_events(self, limit: int = 300) -> list[Message]:
        """Scan recent channel messages and return event-polls the user is attending."""
        attended: list[Message] = []
        async for msg in self._client.iter_messages(self._channel, limit=limit):
            if msg.message and is_event_poll(msg.message) and user_is_attending(msg.message, self._username):
                attended.append(msg)
        logger.info('Scan complete: %d attended event(s) found in last %d messages', len(attended), limit)
        return attended

    def on_vote(self, callback: VoteCallback):
        """
        Fire callback when a channel message is edited and the user's vote
        appears in the attending section.  The domigri bot edits the message
        text to add @username when a button is clicked.
        """
        @self._client.on(events.MessageEdited(chats=self._channel))
        async def _handler(event):
            msg = event.message
            if not msg.message:
                return
            if is_event_poll(msg.message) and user_is_attending(msg.message, self._username):
                await callback(msg)

    async def run(self):
        await self._client.run_until_disconnected()
