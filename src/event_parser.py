import re
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Ukrainian month stems. domigri uses full genitive forms ("квітня") but also
# abbreviations ("листоп."), so match any word starting with a stem.
_UA_MONTH_STEMS: dict[str, int] = {
    'січ': 1, 'лют': 2, 'берез': 3, 'квіт': 4,
    'трав': 5, 'черв': 6, 'лип': 7, 'серп': 8,
    'верес': 9, 'жовт': 10, 'лист': 11, 'груд': 12,
}


def _month_from_word(word: str) -> Optional[int]:
    word = word.lower().rstrip('.')
    for stem, num in _UA_MONTH_STEMS.items():
        if word.startswith(stem):
            return num
    return None

# First line format: "Game Title  ЧТ 30 квітня 18-00" (1 or 2 spaces before DOW)
# Anchor on the day-of-week abbreviation so spacing doesn't matter.
_DOW = r'(?:ПН|ВТ|СР|ЧТ|ПТ|СБ|НД)'
_HEADER_RE = re.compile(
    r'^(.+?)\s+'                                  # title
    + _DOW + r'\s+'                               # day-of-week (required anchor)
    r'(\d{1,2})\s+'                              # day
    r'((?:' + '|'.join(_UA_MONTH_STEMS) + r')[а-яіїєґʼ\']*\.?)'  # month: full or abbreviated
    r'(?:\s+(\d{4}))?\s+'                        # optional year
    r'(\d{1,2})[-:Hh](\d{2})',                   # time  HH-MM / HH:MM
    re.IGNORECASE,
)


@dataclass
class EventInfo:
    title: str
    start_dt: Optional[datetime] = None
    description: str = ''


def parse_event_message(text: str, tz_name: str = 'Europe/Kyiv') -> EventInfo:
    """Parse a domigri event-poll message into structured event info."""
    first_line = text.splitlines()[0].strip()
    m = _HEADER_RE.match(first_line)

    if not m:
        logger.warning('Could not parse header line: %r', first_line)
        return EventInfo(title=first_line, description=text)

    title  = m.group(1).strip()
    day    = int(m.group(2))
    month  = _month_from_word(m.group(3))
    year   = int(m.group(4)) if m.group(4) else _infer_year(month)
    hour   = int(m.group(5))
    minute = int(m.group(6))

    tz = ZoneInfo(tz_name)
    try:
        start_dt = datetime(year, month, day, hour, minute, tzinfo=tz)
    except ValueError as exc:
        logger.error('Bad date constructed from %r: %s', first_line, exc)
        start_dt = None

    return EventInfo(title=title, start_dt=start_dt, description=text)


def _infer_year(month: int) -> int:
    """Pick the nearest future year for a given month."""
    now = datetime.now()
    year = now.year
    if month < now.month:
        year += 1
    return year


def is_event_poll(text: str) -> bool:
    """Return True if the message looks like a domigri event-poll."""
    return 'public poll' in text and 'Я прийду' in text


def user_is_attending(text: str, username: str) -> bool:
    """
    Return True if @username appears in the 'Я прийду' (attending) section,
    not in the 'Місць немає' (waitlist) section.
    """
    handle = f'@{username.lstrip("@")}'
    attending_pos = text.find('Я прийду')
    waitlist_pos  = text.find('Місць немає')

    if attending_pos == -1:
        return False

    attending_section = (
        text[attending_pos:waitlist_pos] if waitlist_pos != -1
        else text[attending_pos:]
    )
    return handle in attending_section
