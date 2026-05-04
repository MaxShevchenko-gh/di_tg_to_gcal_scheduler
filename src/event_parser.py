import re
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Ukrainian month names (genitive case, as used in domigri dates)
_UA_MONTHS: dict[str, int] = {
    'січня': 1, 'лютого': 2, 'березня': 3, 'квітня': 4,
    'травня': 5, 'червня': 6, 'липня': 7, 'серпня': 8,
    'вересня': 9, 'жовтня': 10, 'листопада': 11, 'грудня': 12,
}

# First line format: "Game Title  ЧТ 30 квітня 18-00" (1 or 2 spaces before DOW)
# Anchor on the day-of-week abbreviation so spacing doesn't matter.
_DOW = r'(?:ПН|ВТ|СР|ЧТ|ПТ|СБ|НД)'
_HEADER_RE = re.compile(
    r'^(.+?)\s+'                                  # title
    + _DOW + r'\s+'                               # day-of-week (required anchor)
    r'(\d{1,2})\s+'                              # day
    r'(' + '|'.join(_UA_MONTHS) + r')'           # month name
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
    month  = _UA_MONTHS[m.group(3).lower()]
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
