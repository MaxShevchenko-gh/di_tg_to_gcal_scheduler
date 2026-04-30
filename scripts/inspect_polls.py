"""
Diagnostic: print raw poll data for every poll found in the channel.
Helps identify the structure and whether 'chosen' is populated correctly.

    python scripts/inspect_polls.py
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPoll

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CHANNEL  = os.getenv('TELEGRAM_CHANNEL', 'domigri')
LIMIT    = int(os.getenv('SCAN_LIMIT', '300'))


async def main():
    session_path = os.path.join(DATA_DIR, 'telegram_session')
    api_id   = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']

    async with TelegramClient(session_path, api_id, api_hash) as client:
        print(f'Scanning last {LIMIT} messages in @{CHANNEL}…\n')

        poll_count = 0
        async for msg in client.iter_messages(CHANNEL, limit=LIMIT):
            if not isinstance(msg.media, MessageMediaPoll):
                continue

            poll_count += 1
            poll    = msg.media.poll
            results = msg.media.results

            q = poll.question
            question_text = q.text if hasattr(q, 'text') else str(q)

            print(f'{"─" * 60}')
            print(f'Message ID : {msg.id}  |  Date: {msg.date}')
            print(f'Question   : {question_text[:120]}')
            print(f'Msg text   : {(msg.message or "")[:120]}')
            print()

            # Answers
            print('  Answers:')
            for i, ans in enumerate(poll.answers):
                ans_text = ans.text.text if hasattr(ans.text, 'text') else str(ans.text)
                print(f'    [{i}] {ans_text}')

            # Results
            print('  Results:')
            if results is None:
                print('    results = None')
            elif results.results is None:
                print('    results.results = None')
                print(f'    results raw: {results}')
            else:
                for i, r in enumerate(results.results):
                    ans_text = poll.answers[i].text
                    ans_text = ans_text.text if hasattr(ans_text, 'text') else str(ans_text)
                    chosen = getattr(r, 'chosen', '(attr missing)')
                    correct = getattr(r, 'correct', None)
                    voters  = getattr(r, 'voters', '?')
                    print(f'    [{i}] chosen={chosen}  voters={voters}  correct={correct}  text={ans_text}')

            print()

        if poll_count == 0:
            print('No poll messages found in the last', LIMIT, 'messages.')
        else:
            print(f'Total polls found: {poll_count}')


asyncio.run(main())
