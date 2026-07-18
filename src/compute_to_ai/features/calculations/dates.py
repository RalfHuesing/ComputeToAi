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
