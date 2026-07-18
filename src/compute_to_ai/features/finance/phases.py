"""Standard life-phase sequences for the finance feature.

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/05-Feature-Finanzen-Parameter.md.
"""

from compute_to_ai.engine.timeline import Phase


def build_standard_life_phases(
    current_age: int,
    employment_end_age: int,
    statutory_pension_start_age: int,
    life_expectancy_age: int,
    education_end_age: int | None = None,
    education_phase_name: str = "Ausbildung",
    employment_phase_name: str = "Erwerbsphase",
    early_retirement_gap_phase_name: str = "Frühruhestandslücke",
    pension_phase_name: str = "Rentenphase",
) -> list[Phase]:
    """Build the standard life-phase sequence (Docs/05, "Lebensphasen").

    Step 0 corresponds to `current_age`; each step is one year. An optional
    education phase runs first, then an employment phase until
    `employment_end_age`, an optional early-retirement gap if employment
    ends before `statutory_pension_start_age`, and finally a pension phase
    until `life_expectancy_age`. Phase names are plain, freely renameable
    labels (see Docs/01-Kern-Domaenenmodell.md, "Phase") - nothing in the
    engine or in other finance building blocks inspects them by name.
    """
    phases: list[Phase] = []
    step = 0

    if education_end_age is not None and education_end_age > current_age:
        education_end_step = education_end_age - current_age
        phases.append(
            Phase(name=education_phase_name, start_step=step, end_step=education_end_step)
        )
        step = education_end_step

    employment_end_step = employment_end_age - current_age
    phases.append(
        Phase(name=employment_phase_name, start_step=step, end_step=employment_end_step)
    )
    step = employment_end_step

    pension_start_step = statutory_pension_start_age - current_age
    if pension_start_step > step:
        phases.append(
            Phase(
                name=early_retirement_gap_phase_name,
                start_step=step,
                end_step=pension_start_step,
            )
        )
        step = pension_start_step

    life_expectancy_step = life_expectancy_age - current_age
    phases.append(Phase(name=pension_phase_name, start_step=step, end_step=life_expectancy_step))

    return phases
