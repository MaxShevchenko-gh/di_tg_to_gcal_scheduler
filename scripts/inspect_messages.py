"""
Dump recent channel messages so you can identify which ones are events
and how they are structured.

    python scripts/inspect_messages.py
    python scripts/inspect_messages.py 50      # show last 50 messages (default 30)
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl import types

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CHANNEL  = os.getenv('TELEGRAM_CHANNEL', 'domigri')
LIMIT    = int(sys.argv[1]) if len(sys.argv) > 1 else 30


async def main():
    session_path = os.path.join(DATA_DIR, 'telegram_session')
    api_id   = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']

    async with TelegramClient(session_path, api_id, api_hash) as client:
        print(f'Last {LIMIT} messages from @{CHANNEL}\n')

        async for msg in client.iter_messages(CHANNEL, limit=LIMIT):
            print(f'{"═" * 60}')
            print(f'ID: {msg.id}   Date: {msg.date}   Media: {type(msg.media).__name__}')

            if msg.message:
                print(f'Text:\n{msg.message}')

            # Inline keyboard / reply buttons
            if msg.reply_markup:
                markup = msg.reply_markup
                print(f'Buttons ({type(markup).__name__}):')
                if hasattr(markup, 'rows'):
                    for row in markup.rows:
                        for btn in row.buttons:
                            label = getattr(btn, 'text', '')
                            data  = getattr(btn, 'data', None)
                            url   = getattr(btn, 'url', None)
                            extra = f'data={data}' if data else (f'url={url}' if url else '')
                            print(f'  [{label}]  {extra}')

            # Poll (native Telegram poll)
            if isinstance(msg.media, types.MessageMediaPoll):
                poll = msg.media.poll
                q = poll.question
                print(f'Poll question: {q.text if hasattr(q, "text") else q}')
                for i, ans in enumerate(poll.answers):
                    t = ans.text.text if hasattr(ans.text, 'text') else str(ans.text)
                    r = (msg.media.results.results or [])[i] if msg.media.results and msg.media.results.results else None
                    chosen  = getattr(r, 'chosen', '?') if r else '?'
                    voters  = getattr(r, 'voters', '?') if r else '?'
                    print(f'  [{i}] chosen={chosen} voters={voters}  {t}')

            # Web preview / link
            if isinstance(msg.media, types.MessageMediaWebPage):
                wp = msg.media.webpage
                if hasattr(wp, 'title'):
                    print(f'Link preview: {wp.title}  {getattr(wp, "url", "")}')

            # Photo/document
            if isinstance(msg.media, types.MessageMediaPhoto):
                print('(photo)')
            if isinstance(msg.media, types.MessageMediaDocument):
                print('(document/file)')

            print()


asyncio.run(main())
