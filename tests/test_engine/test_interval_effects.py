"""Tests for interval-based effect occurrences in the simulation engine.

See Docs/01-Kern-Domaenenmodell.md and tasks/task-4.11-frequenz-und-intervall-ausgaben/.
"""

from compute_to_ai.engine.effect import BaseEffect, GrowingFixedEffect


def test_default_interval_effect() -> None:
    """Default effect has interval_steps=1, first_occurrence_step=0 and is active every step."""
    effect = BaseEffect()
    assert effect.interval_steps == 1
    assert effect.first_occurrence_step == 0
    for step in range(10):
        assert effect.is_active(step, None) is True
        assert effect.is_active_at_step(step) is True


def test_yearly_interval_effect() -> None:
    """Effect with interval_steps=12 is active only every 12 steps."""
    effect = BaseEffect(interval_steps=12, first_occurrence_step=0)
    for step in range(36):
        if step % 12 == 0:
            assert effect.is_active(step, None) is True
        else:
            assert effect.is_active(step, None) is False


def test_offset_first_occurrence() -> None:
    """Effect starting at step 3 with interval 6 is active at 3, 9, 15, 21..."""
    effect = BaseEffect(interval_steps=6, first_occurrence_step=3)
    active_steps = [s for s in range(25) if effect.is_active(s, None)]
    assert active_steps == [3, 9, 15, 21]


def test_interval_combined_with_start_end_steps() -> None:
    """Interval effect respects start_step and end_step boundaries."""
    effect = GrowingFixedEffect(
        store_name="cash",
        amount_per_step=-1000.0,
        interval_steps=6,
        first_occurrence_step=3,
        start_step=5,
        end_step=20,
    )
    # Step 3 is before start_step=5 -> inactive
    assert effect.is_active(3, None) is False
    # Step 9 and 15 are in [5, 20] and match (s-3)%6==0 -> active
    assert effect.is_active(9, None) is True
    assert effect.is_active(15, None) is True
    # Step 21 is after end_step=20 -> inactive
    assert effect.is_active(21, None) is False


def test_interval_combined_with_active_phases() -> None:
    """Interval effect respects phase restrictions."""
    effect = BaseEffect(
        interval_steps=3,
        first_occurrence_step=0,
        active_phases=["retirement"],
    )
    # Step 0 matches interval, but phase is "work" -> inactive
    assert effect.is_active(0, "work") is False
    # Step 0 matches interval and phase is "retirement" -> active
    assert effect.is_active(0, "retirement") is True
    # Step 1 does not match interval -> inactive even in retirement
    assert effect.is_active(1, "retirement") is False
