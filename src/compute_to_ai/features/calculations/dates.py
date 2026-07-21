"""Date and age arithmetic - see Docs/06-Feature-Berechnungen.md."""

from datetime import date


def years_between(start: date, end: date) -> float:
    """Fractional number of years between two dates (365.25-day year)."""
    if end < start:
        msg = f"end {end} is before start {start}"
        raise ValueError(msg)
    return (end - start).days / 365.25


def age_in_years(birth_date: date, as_of: date) -> int:
    """Whole years of age on as_of, accounting for whether that year's
    birthday has already happened."""
    if as_of < birth_date:
        msg = f"as_of {as_of} is before birth_date {birth_date}"
        raise ValueError(msg)
    years = as_of.year - birth_date.year
    had_birthday_this_year = (as_of.month, as_of.day) >= (birth_date.month, birth_date.day)
    return years if had_birthday_this_year else years - 1


def step_to_age(step: int, current_age: int, steps_per_year: int = 1) -> float:
    """Age at a given simulation step, given step 0 == current_age - translates
    a Plan's 0-based step index into the age a human thinks in.

    `steps_per_year` makes the conversion explicit instead of assuming a
    fixed one-step-one-year cadence (see Timeline.steps_per_year,
    Docs/01-Kern-Domaenenmodell.md, "Zeitstrahl"). The result is fractional
    when `step` is not a whole multiple of `steps_per_year` (e.g. step 6 on
    a monthly-step plan is half a year past `current_age`).
    """
    if step < 0:
        msg = f"step must be >= 0, got {step}"
        raise ValueError(msg)
    if steps_per_year <= 0:
        msg = f"steps_per_year must be > 0, got {steps_per_year}"
        raise ValueError(msg)
    return current_age + step / steps_per_year


def age_to_step(age: float, current_age: int, steps_per_year: int = 1) -> int:
    """Inverse of step_to_age: the (rounded) step at which a given age is reached."""
    if age < current_age:
        msg = f"age {age} is before current_age {current_age}"
        raise ValueError(msg)
    if steps_per_year <= 0:
        msg = f"steps_per_year must be > 0, got {steps_per_year}"
        raise ValueError(msg)
    return round((age - current_age) * steps_per_year)
