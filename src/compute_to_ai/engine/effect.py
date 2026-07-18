"""Effect models and computed effect registry.

See Docs/01-Kern-Domaenenmodell.md and Docs/11-Code-Standards-und-Projektstruktur.md.
"""

from collections.abc import Callable
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field
from pydantic import Field as PydanticField


class BaseEffect(BaseModel):
    """Common base for all simulation effects."""

    name: str | None = Field(default=None, description="Optional custom name of this effect")
    start_step: int | None = Field(default=None, description="Start step (inclusive)")
    end_step: int | None = Field(default=None, description="End step (inclusive)")
    active_phases: list[str] | None = Field(
        default=None, description="List of phase names this effect is active in"
    )

    def is_active(self, step: int, active_phase_name: str | None) -> bool:
        """Check if the effect is active at a given step and active phase."""
        if self.start_step is not None and step < self.start_step:
            return False
        if self.end_step is not None and step > self.end_step:
            return False
        return not (
            self.active_phases is not None
            and (active_phase_name is None or active_phase_name not in self.active_phases)
        )


class GrowingFixedEffect(BaseEffect):
    """An additive effect that grows at a fixed rate per step.

    Decks income, expenses, loan payments, lump-sum acquisitions, etc.
    """

    type: Literal["growing_fixed"] = "growing_fixed"
    store_name: str
    amount_per_step: float
    growth_rate: float = 0.0


class PercentageGrowthEffect(BaseEffect):
    """A compounding growth effect that grows a store's balance by a rate."""

    type: Literal["percentage_growth"] = "percentage_growth"
    store_name: str
    growth_rate: float


class CorrelatedReturnEffect(BaseEffect):
    """A stochastic growth effect whose rate is drawn from a multivariate normal distribution.

    Drawn together with all other effects in the same correlation group.
    """

    type: Literal["correlated_return"] = "correlated_return"
    store_name: str
    correlation_group: str
    expected_return: float
    volatility: float


class ComputedEffect(BaseEffect):
    """A dynamic effect executed at Phase 2 of each step, calling registered Python code."""

    type: Literal["computed"] = "computed"
    store_name: str | None = None
    function_name: str
    parameters: dict[str, Any] = {}


# Discriminated Union for Pydantic to cleanly serialize/deserialize effects
Effect = Annotated[
    GrowingFixedEffect | PercentageGrowthEffect | CorrelatedReturnEffect | ComputedEffect,
    PydanticField(discriminator="type"),
]

# Computed function registry
# Signature: func(balances, step, parameters, plan) -> None
# It mutates the balances dictionary in-place.
ComputedFunction = Callable[[dict[str, float], int, dict[str, Any], Any], None]
COMPUTED_EFFECT_REGISTRY: dict[str, ComputedFunction] = {}


def register_computed_effect(name: str) -> Callable[[ComputedFunction], ComputedFunction]:
    """Decorator to register a custom computed effect function."""

    def decorator(func: ComputedFunction) -> ComputedFunction:
        COMPUTED_EFFECT_REGISTRY[name] = func
        return func

    return decorator
