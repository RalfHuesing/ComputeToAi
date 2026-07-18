from datetime import date

import pytest

from compute_to_ai.features.calculations.dates import (
    age_in_years,
    age_to_step,
    step_to_age,
    years_between,
)


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


def test_step_to_age_is_current_age_at_step_zero() -> None:
    assert step_to_age(0, current_age=47) == 47


def test_step_to_age_adds_steps_as_years() -> None:
    assert step_to_age(20, current_age=47) == 67


def test_step_to_age_rejects_negative_step() -> None:
    with pytest.raises(ValueError, match="step"):
        step_to_age(-1, current_age=47)


def test_age_to_step_is_inverse_of_step_to_age() -> None:
    assert age_to_step(67, current_age=47) == 20


def test_age_to_step_rejects_age_before_current_age() -> None:
    with pytest.raises(ValueError, match="before current_age"):
        age_to_step(40, current_age=47)
