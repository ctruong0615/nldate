"""Parse common English date expressions into datetime.date objects."""

import re
from datetime import date, datetime, timedelta

from dateutil import parser as date_parser  # type: ignore[import-untyped]
from dateutil.relativedelta import relativedelta  # type: ignore[import-untyped]

_WEEKDAYS = {
    name: index
    for index, name in enumerate(
        (
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        )
    )
}

_NUMBERS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}

_DURATION_PART = re.compile(
    r"\b(\d+|[a-z]+(?:-[a-z]+)?)\s+"
    r"(years?|months?|weeks?|days?)\b"
)


def _amount(value: str) -> int | None:
    if value.isdecimal():
        return int(value)
    if value in _NUMBERS:
        return _NUMBERS[value]
    pieces = value.split("-")
    if len(pieces) == 2 and all(piece in _NUMBERS for piece in pieces):
        return _NUMBERS[pieces[0]] + _NUMBERS[pieces[1]]
    return None


def _duration(value: str) -> relativedelta | None:
    matches = list(_DURATION_PART.finditer(value))
    if not matches:
        return None

    leftover = _DURATION_PART.sub(" ", value)
    leftover = re.sub(r"\b(and)\b|,", " ", leftover).strip()
    if leftover:
        return None

    units = {
        "years": 0,
        "months": 0,
        "weeks": 0,
        "days": 0,
    }

    for match in matches:
        count = _amount(match.group(1))
        if count is None:
            return None
        unit = match.group(2).removesuffix("s") + "s"
        units[unit] += count

    return relativedelta(**units)


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date string."""
    if not isinstance(s, str) or not s.strip():
        raise ValueError("A nonempty date string is required")

    reference = today if today is not None else date.today()
    value = " ".join(s.lower().strip().split())
    value = re.sub(r"^the\s+", "", value)

    simple = {
        "today": reference,
        "tomorrow": reference + timedelta(days=1),
        "yesterday": reference - timedelta(days=1),
        "now": reference,
        "day after tomorrow": reference + timedelta(days=2),
        "day before yesterday": reference - timedelta(days=2),
    }

    if value in simple:
        return simple[value]

    weekday = re.fullmatch(
        r"(next|last|this)\s+"
        r"(monday|tuesday|wednesday|thursday|"
        r"friday|saturday|sunday)",
        value,
    )

    if weekday:
        modifier, name = weekday.groups()
        difference = _WEEKDAYS[name] - reference.weekday()

        if modifier == "next":
            difference = difference % 7 or 7
        elif modifier == "last":
            difference = -((-difference) % 7 or 7)

        return reference + timedelta(days=difference)

    if value in _WEEKDAYS:
        offset = (_WEEKDAYS[value] - reference.weekday()) % 7
        return reference + timedelta(days=offset)

    period = re.fullmatch(
        r"(next|last|this)\s+(day|week|month|year)",
        value,
    )

    if period:
        modifier, unit = period.groups()
        count = 1 if modifier == "next" else -1 if modifier == "last" else 0
        return reference + relativedelta(**{unit + "s": count})

    anchored = re.fullmatch(
        r"(.+?)\s+(before|after|from)\s+(.+)",
        value,
    )

    if anchored:
        amount, operation, target = anchored.groups()
        delta = _duration(amount)

        if delta is not None:
            anchor = parse(target, reference)
            if operation == "before":
                return anchor - delta
            return anchor + delta

    if value.startswith("in "):
        delta = _duration(value[3:])
        if delta is not None:
            return reference + delta

    for ending, sign in (
        (" ago", -1),
        (" from now", 1),
        (" from today", 1),
        (" later", 1),
    ):
        if value.endswith(ending):
            delta = _duration(value[: -len(ending)])
            if delta is not None:
                if sign < 0:
                    return reference - delta
                return reference + delta

    cleaned = re.sub(
        r"\b(\d{1,2})(st|nd|rd|th)\b",
        r"\1",
        value,
    )

    if re.search(r"[a-z/-]", cleaned):
        try:
            result = date_parser.parse(
                cleaned,
                default=datetime(reference.year, 1, 1),
                fuzzy=False,
            )
            return result.date()
        except (ValueError, OverflowError):
            pass

    raise ValueError(f"Unrecognized date: {s!r}")
