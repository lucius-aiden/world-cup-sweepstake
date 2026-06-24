from datetime import UTC, datetime

from src.daily_message import should_generate_daily_message


def test_daily_message_runs_once_on_weekday_at_seven_am_uk_time():
    assert should_generate_daily_message(
        now=datetime(2026, 6, 23, 6, 0, tzinfo=UTC),
        timezone_name="Europe/London",
        last_generated_for_date=None,
        target_hour=7,
    ) is True
    assert should_generate_daily_message(
        now=datetime(2026, 6, 23, 6, 0, tzinfo=UTC),
        timezone_name="Europe/London",
        last_generated_for_date="2026-06-23",
        target_hour=7,
    ) is False


def test_daily_message_skips_weekends_and_non_target_refreshes():
    assert should_generate_daily_message(
        now=datetime(2026, 6, 27, 6, 0, tzinfo=UTC),
        timezone_name="Europe/London",
        last_generated_for_date=None,
        target_hour=7,
    ) is False
    assert should_generate_daily_message(
        now=datetime(2026, 6, 23, 5, 45, tzinfo=UTC),
        timezone_name="Europe/London",
        last_generated_for_date=None,
        target_hour=7,
    ) is False
    assert should_generate_daily_message(
        now=datetime(2026, 6, 23, 6, 15, tzinfo=UTC),
        timezone_name="Europe/London",
        last_generated_for_date=None,
        target_hour=7,
    ) is False
