from itertools import pairwise

import pytest

from compute_to_ai.features.finance.phases import build_standard_life_phases


def test_standard_phases_with_early_retirement_gap() -> None:
    phases = build_standard_life_phases(
        current_age=20,
        employment_end_age=63,
        statutory_pension_start_age=67,
        life_expectancy_age=90,
    )

    assert [(p.name, p.start_step, p.end_step) for p in phases] == [
        ("Erwerbsphase", 0, 43),
        ("Frühruhestandslücke", 43, 47),
        ("Rentenphase", 47, 70),
    ]


def test_standard_phases_with_education_and_no_gap() -> None:
    phases = build_standard_life_phases(
        current_age=25,
        employment_end_age=67,
        statutory_pension_start_age=67,
        life_expectancy_age=90,
        education_end_age=29,
    )

    # No early-retirement gap: employment ends exactly at the statutory pension start.
    assert [(p.name, p.start_step, p.end_step) for p in phases] == [
        ("Ausbildung", 0, 4),
        ("Erwerbsphase", 4, 42),
        ("Rentenphase", 42, 65),
    ]


def test_standard_phases_are_contiguous_and_gapless() -> None:
    phases = build_standard_life_phases(
        current_age=18,
        employment_end_age=65,
        statutory_pension_start_age=70,
        life_expectancy_age=95,
        education_end_age=22,
    )

    for earlier, later in pairwise(phases):
        assert earlier.end_step == later.start_step
    assert phases[0].start_step == 0
    assert phases[-1].end_step == 95 - 18


def test_standard_phases_with_monthly_steps_scale_boundaries() -> None:
    phases = build_standard_life_phases(
        current_age=30,
        employment_end_age=67,
        statutory_pension_start_age=67,
        life_expectancy_age=85,
        steps_per_year=12,
    )

    assert [(p.name, p.start_step, p.end_step) for p in phases] == [
        ("Erwerbsphase", 0, (67 - 30) * 12),
        ("Rentenphase", (67 - 30) * 12, (85 - 30) * 12),
    ]


def test_standard_phases_with_explicit_annual_steps_match_default() -> None:
    explicit = build_standard_life_phases(
        current_age=20,
        employment_end_age=63,
        statutory_pension_start_age=67,
        life_expectancy_age=90,
        steps_per_year=1,
    )
    default = build_standard_life_phases(
        current_age=20,
        employment_end_age=63,
        statutory_pension_start_age=67,
        life_expectancy_age=90,
    )
    assert explicit == default


def test_standard_phases_reject_non_positive_steps_per_year() -> None:
    with pytest.raises(ValueError, match="steps_per_year"):
        build_standard_life_phases(
            current_age=20,
            employment_end_age=63,
            statutory_pension_start_age=67,
            life_expectancy_age=90,
            steps_per_year=0,
        )
