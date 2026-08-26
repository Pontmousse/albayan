"""تنسيق التواريخ الظاهرة للمستخدم بالهجري (أم القرى)."""

from __future__ import annotations

from datetime import UTC, datetime, timezone

from hijridate import Gregorian

_ARABIC_INDIC = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def _to_utc_calendar(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)
    return value.replace(tzinfo=UTC)


def _arabic_indic(text: str) -> str:
    return text.translate(_ARABIC_INDIC)


def format_date(value: datetime) -> str:
    """Hijri Umm al-Qura date, Arabic-Indic digits, e.g. ١٣ ربيع الأول ١٤٤٨ هـ"""
    utc = _to_utc_calendar(value)
    hijri = Gregorian(utc.year, utc.month, utc.day).to_hijri()
    day = _arabic_indic(str(hijri.day))
    month = hijri.month_name("ar")
    year = _arabic_indic(str(hijri.year))
    notation = hijri.notation("ar")
    return f"{day} {month} {year} {notation}"


def format_date_time(value: datetime) -> str:
    """format_date plus time of day, e.g. ١٣ ربيع الأول ١٤٤٨ هـ، ١٤:٣٠"""
    utc = _to_utc_calendar(value)
    date_part = format_date(value)
    time_part = _arabic_indic(f"{utc.hour:02d}:{utc.minute:02d}")
    return f"{date_part}، {time_part}"
