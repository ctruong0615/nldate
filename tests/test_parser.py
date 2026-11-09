from datetime import date, timedelta

import pytest

from nldate import parse

REFERENCE_DATE = date(2025, 5, 14)


def test_today():
    assert parse("today", REFERENCE_DATE) == REFERENCE_DATE


def test_tomorrow():
    assert parse("tomorrow", REFERENCE_DATE) == date(2025, 5, 15)


def test_yesterday():
    assert parse("yesterday", REFERENCE_DATE) == date(2025, 5, 13)


def test_in_three_days():
    assert parse("in 3 days", REFERENCE_DATE) == date(2025, 5, 17)


def test_five_days_ago():
    assert parse("5 days ago", REFERENCE_DATE) == date(2025, 5, 9)


def test_next_tuesday():
    assert parse("next Tuesday", REFERENCE_DATE) == date(2025, 5, 20)


def test_last_friday():
    assert parse("last Friday", REFERENCE_DATE) == date(2025, 5, 9)


def test_full_date():
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_iso_date():
    assert parse("2025-12-01") == date(2025, 12, 1)


def test_numeric_date():
    assert parse("12/01/2025") == date(2025, 12, 1)


def test_days_before_date():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_two_weeks_from_tomorrow():
    assert parse("two weeks from tomorrow", REFERENCE_DATE) == date(2025, 5, 29)


def test_complex_relative_date():
    assert parse("1 year and 2 months after yesterday", REFERENCE_DATE) == date(
        2026, 7, 13
    )


def test_case_insensitive():
    assert parse("TOMORROW", REFERENCE_DATE) == date(2025, 5, 15)


def test_empty_string():
    with pytest.raises(ValueError):
        parse("")


def test_invalid_string():
    with pytest.raises(ValueError):
        parse("this is not a date")


def test_default_today():
    assert parse("today") == date.today()


def test_default_tomorrow():
    assert parse("tomorrow") == date.today() + timedelta(days=1)
