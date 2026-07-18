from datetime import date

import pytest

from compute_to_ai.features.calculations.dates import age_in_years, years_between


def test_years_between_ten_calendar_years() -> None:
    result = years_between(date(2020, 1, 1), date(2030, 1, 1))

    assert result == pytest.approx(10.0, abs=0.01)


def test_years_between_rejects_end_before_start() -> None:
    with pytest.raises(ValueError, match="before start"):
        years_between(date(2030, 1, 1), date(2020, 1, 1))


def test_age_in_years_before_birthday_this_year() -> None:
    assert age_in_years(date(1980, 7, 20), date(2026, 7, 18)) == 45


def test_age_in_years_on_birthday() -> None:
    assert age_in_years(date(1980, 7, 18), date(2026, 7, 18)) == 46


def test_age_in_years_after_birthday_this_year() -> None:
    assert age_in_years(date(1980, 7, 1), date(2026, 7, 18)) == 46


def test_age_in_years_rejects_as_of_before_birth() -> None:
    with pytest.raises(ValueError, match="before birth_date"):
        age_in_years(date(2026, 1, 1), date(2000, 1, 1))
