import unittest
from datetime import UTC, datetime
from pathlib import Path


class DatesHelperTests(unittest.TestCase):
    def test_format_date_umm_al_qura_arabic_indic(self) -> None:
        from app.core.dates import format_date

        value = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
        self.assertEqual(format_date(value), "١٣ ربيع الأول ١٤٤٨ هـ")

    def test_format_date_time_includes_arabic_indic_clock(self) -> None:
        from app.core.dates import format_date, format_date_time

        value = datetime(2026, 8, 26, 12, 0, tzinfo=UTC)
        result = format_date_time(value)
        self.assertIn(format_date(value), result)
        self.assertIn("١٢:٠٠", result)
        self.assertIn("،", result)
        self.assertNotIn("UTC", result)

    def test_email_service_uses_format_date_time_not_strftime(self) -> None:
        source = Path(__file__).resolve().parents[1] / "app" / "services" / "email_service.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn("format_date_time", text)
        self.assertNotIn("strftime", text)


if __name__ == "__main__":
    unittest.main()
