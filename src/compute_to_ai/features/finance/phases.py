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
    timeline_step_count: int | None = None,
    steps_per_year: int = 1,
) -> list[Phase]:
    """Build the standard life-phase sequence (Docs/05, "Lebensphasen").

    Step 0 corresponds to `current_age`; every age difference is converted
    into steps via `steps_per_year` (see Timeline.steps_per_year,
    Docs/01-Kern-Domaenenmodell.md, "Zeitstrahl"). An optional education
    phase runs first, then an employment phase ending at step
    `(employment_end_age - current_age) * steps_per_year` (exclusive, i.e.,
    employment income ends one step earlier and retirement starts at that
    step), an optional early-retirement gap if employment ends before
    `statutory_pension_start_age`, and finally a pension phase until
    `life_expectancy_age` (or `timeline_step_count` if provided;
    `timeline_step_count` is already a step count, never scaled).
    Phase names are plain, freely renameable labels (see Docs/01-Kern-Domaenenmodell.md, "Phase").
    """
    if steps_per_year <= 0:
        msg = f"steps_per_year must be > 0, got {steps_per_year}"
        raise ValueError(msg)

    phases: list[Phase] = []
    step = 0

    if education_end_age is not None and education_end_age > current_age:
        education_end_step = (education_end_age - current_age) * steps_per_year
        phases.append(
            Phase(name=education_phase_name, start_step=step, end_step=education_end_step)
        )
        step = education_end_step

    employment_end_step = (employment_end_age - current_age) * steps_per_year
    phases.append(Phase(name=employment_phase_name, start_step=step, end_step=employment_end_step))
    step = employment_end_step

    pension_start_step = (statutory_pension_start_age - current_age) * steps_per_year
    if pension_start_step > step:
        phases.append(
            Phase(
                name=early_retirement_gap_phase_name,
                start_step=step,
                end_step=pension_start_step,
            )
        )
        step = pension_start_step

    life_expectancy_step = (life_expectancy_age - current_age) * steps_per_year
    if timeline_step_count is not None:
        final_end_step = max(life_expectancy_step, timeline_step_count)
    else:
        final_end_step = life_expectancy_step

    phases.append(Phase(name=pension_phase_name, start_step=step, end_step=final_end_step))

    return phases
