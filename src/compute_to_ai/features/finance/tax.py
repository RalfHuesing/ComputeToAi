"""German taxation system (Abgeltungsteuer, Sparerpauschbetrag, Vorabpauschale, rent tax).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from pydantic import BaseModel

from compute_to_ai.engine.effect import ComputedEffect, register_computed_effect
from compute_to_ai.engine.plan import Plan


class IncomeTaxTariff(BaseModel):
    """A § 32a EStG-shaped progressive income tax tariff.

    The five-zone shape (exempt, two quadratic brackets, two linear top
    brackets) has been structurally stable for decades; only the bracket
    boundaries and coefficients change from one tax year to the next. Every
    such number is a field here rather than a Python literal, so switching to
    a different year's tariff never requires a code change - only a
    different `IncomeTaxTariff` instance. Defaults are the sourced 2026
    values (see Docs/09-Quellen.md); a full mechanism for automatically
    switching tariffs mid-simulation is out of scope (see Meilenstein 4 in
    Docs/10-Roadmap.md).
    """

    basic_allowance: float = 12348.0
    zone2_upper_bound: float = 17799.0
    zone2_coefficient: float = 914.51
    zone2_constant: float = 1400.0
    zone3_upper_bound: float = 69878.0
    zone3_coefficient: float = 173.10
    zone3_constant: float = 2397.0
    zone3_offset: float = 1034.87
    zone4_upper_bound: float = 277825.0
    zone4_rate: float = 0.42
    zone4_subtract: float = 11135.63
    zone5_rate: float = 0.45
    zone5_subtract: float = 19470.38


def calculate_income_tax(taxable_income: float, tariff: IncomeTaxTariff) -> float:
    """Calculate progressive income tax for a given tariff (§ 32a EStG shape)."""
    zv = taxable_income
    if zv <= tariff.basic_allowance:
        return 0.0

    if zv <= tariff.zone2_upper_bound:
        y = (zv - tariff.basic_allowance) / 10000.0
        return (tariff.zone2_coefficient * y + tariff.zone2_constant) * y

    if zv <= tariff.zone3_upper_bound:
        z = (zv - tariff.zone2_upper_bound) / 10000.0
        return (tariff.zone3_coefficient * z + tariff.zone3_constant) * z + tariff.zone3_offset

    if zv <= tariff.zone4_upper_bound:
        return tariff.zone4_rate * zv - tariff.zone4_subtract

    return tariff.zone5_rate * zv - tariff.zone5_subtract


class AssetClassTaxConfig(BaseModel):
    """Per-asset-class taxation parameters for the capital gains building block."""

    partial_exemption_rate: float = 0.0
    is_accumulating: bool = False
    growth_rate: float = 0.0


class TaxManagerParameters(BaseModel):
    """Parameters for the `tax_manager` computed effect.

    Both `add_tax_manager` (writer) and `tax_manager_func` (reader) validate
    through this single model instead of matching dict-key strings by
    convention, so a typo becomes a validation error instead of a silently
    ignored default.
    """

    cash_store_name: str = "cash"
    sparerpauschbetrag: float = 1000.0
    basiszins: float = 0.032
    withholding_tax_rate: float = 0.25
    soli_rate: float = 0.055
    church_tax_rate: float = 0.0
    tariff: IncomeTaxTariff = IncomeTaxTariff()
    kvdr_rate: float = 0.0875
    pv_rate: float = 0.042
    retirement_step: int = 47
    start_year: int = 2026
    asset_classes: dict[str, AssetClassTaxConfig] = {}


def _apply_pension_taxation(
    balances: dict[str, float], step: int, plan: Plan, params: TaxManagerParameters
) -> None:
    """Calculate and deduct progressive tax and KVdR/PV contributions from pension income.

    Whether pension taxation applies is decided solely by the explicit
    `retirement_step` parameter, never by inspecting a phase's name - a
    Phase's name is an opaque label (see Docs/01-Kern-Domaenenmodell.md).
    """
    if step < params.retirement_step:
        return

    cash_store = params.cash_store_name
    active_phase = plan.get_active_phase_name(step)

    # Sum rent income (positive cashflows from Phase 1)
    rent_income = 0.0
    for effect in plan.effects:
        if (
            effect.is_active(step, active_phase)
            and getattr(effect, "store_name", None) == cash_store
        ):
            amount = getattr(effect, "amount_per_step", 0.0)
            raw_rate = getattr(effect, "growth_rate", 0.0)
            rate = plan.resolve_rate(raw_rate)
            val = amount * ((1.0 + rate) ** step)
            if val > 0.0:
                rent_income += val

    if rent_income <= 0.0:
        return

    # Insurance contributions
    insurance_premium = rent_income * (params.kvdr_rate + params.pv_rate)
    balances[cash_store] = balances.get(cash_store, 0.0) - insurance_premium

    # Taxable share based on retirement year
    retirement_year = params.start_year + params.retirement_step
    taxable_share = min(1.0, 0.84 + 0.005 * (retirement_year - 2026))
    rent_taxable = rent_income * taxable_share

    # Taxable income (Einkommensteuer-Bemessungsgrundlage)
    zv = max(0.0, rent_taxable - params.tariff.basic_allowance - insurance_premium)
    rent_tax = calculate_income_tax(zv, params.tariff)
    balances[cash_store] = balances.get(cash_store, 0.0) - rent_tax


def _calculate_sales_taxable_gains(
    plan: Plan, asset_classes: dict[str, AssetClassTaxConfig]
) -> float:
    """Compute total taxable gains from sales from withdrawn lots during this step."""
    gains_from_sales = 0.0
    for name, ac_cfg in asset_classes.items():
        store = plan.store(name)
        for lot in store.withdrawn_lots_this_step:
            is_pre_2009 = lot.created_step < 0 or lot.rule_version == "pre_2009"
            if not is_pre_2009:
                raw_gain = lot.quantity - lot.cost_basis
                already_taxed = lot.metadata.get("vorabpauschale_taxed", 0.0)
                taxable_gain = max(0.0, raw_gain - already_taxed)
                gains_from_sales += taxable_gain * (1.0 - ac_cfg.partial_exemption_rate)
    return gains_from_sales


def _calculate_vorabpauschale_taxable(
    plan: Plan, asset_classes: dict[str, AssetClassTaxConfig], basiszins: float
) -> float:
    """Calculate the taxable Vorabpauschale on accumulating lots at the end of the year."""
    vorab_taxable_total = 0.0
    for name, ac_cfg in asset_classes.items():
        if not ac_cfg.is_accumulating:
            continue

        store = plan.store(name)

        # Calculate Vorabpauschale on remaining lots at the end of the year
        for lot in store.lots:
            growth_factor = 1.0 + ac_cfg.growth_rate
            q_start = lot.quantity / growth_factor
            actual_growth = lot.quantity - q_start
            potential_vorab = q_start * basiszins * 0.7
            vorab = min(potential_vorab, max(0.0, actual_growth))

            vorab_taxable_total += vorab * (1.0 - ac_cfg.partial_exemption_rate)
            # Track already-taxed gain on the lot to avoid double taxation on sale
            lot.metadata["vorabpauschale_taxed"] = (
                lot.metadata.get("vorabpauschale_taxed", 0.0) + vorab
            )
    return vorab_taxable_total


def _apply_capital_gains_taxation(
    balances: dict[str, float], plan: Plan, params: TaxManagerParameters
) -> None:
    """Calculate and deduct capital gains tax (withholding tax, allowance, Vorabpauschale)."""
    asset_classes = {name: cfg for name, cfg in params.asset_classes.items() if name in balances}

    gains_from_sales = _calculate_sales_taxable_gains(plan, asset_classes)
    vorab_taxable_total = _calculate_vorabpauschale_taxable(plan, asset_classes, params.basiszins)

    # Abgeltungsteuer-Abrechnung
    total_cap_gains = gains_from_sales + vorab_taxable_total
    if total_cap_gains > params.sparerpauschbetrag:
        excess = total_cap_gains - params.sparerpauschbetrag
        eff_rate = params.withholding_tax_rate * (1.0 + params.soli_rate + params.church_tax_rate)
        cap_gains_tax = excess * eff_rate
        cash_store = params.cash_store_name
        balances[cash_store] = balances.get(cash_store, 0.0) - cap_gains_tax


@register_computed_effect("pension_income_tax_manager")
def pension_income_tax_manager_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], step: int, parameters: dict[str, Any], plan: Plan
) -> None:
    """Computed effect implementing progressive pension income taxation."""
    params = TaxManagerParameters.model_validate(parameters)
    _apply_pension_taxation(balances, step, plan, params)


@register_computed_effect("capital_gains_tax_manager")
def capital_gains_tax_manager_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], _step: int, parameters: dict[str, Any], plan: Plan
) -> None:
    """Computed effect implementing capital gains tax (withholding tax, Vorabpauschale)."""
    params = TaxManagerParameters.model_validate(parameters)
    _apply_capital_gains_taxation(balances, plan, params)


def add_tax_manager(
    plan: Plan,
    cash_store_name: str = "cash",
    sparerpauschbetrag: float = 1000.0,
    basiszins: float = 0.032,
    withholding_tax_rate: float = 0.25,
    soli_rate: float = 0.055,
    church_tax_rate: float = 0.0,
    tariff: IncomeTaxTariff | None = None,
    kvdr_rate: float = 0.0875,
    pv_rate: float = 0.042,
    retirement_step: int = 47,
    start_year: int = 2026,
    asset_classes: dict[str, AssetClassTaxConfig] | None = None,
    description: str | None = None,
) -> None:
    """Add a computed tax manager to the plan.

    `cash_store_name` and every key in `asset_classes` reference existing
    Stores and are validated up front - a typo'd cash store would otherwise
    accumulate tax deductions in a phantom balance that is never written
    back to the plan, and a typo'd asset class key would only fail at
    simulation time.
    """
    plan.validate_store_names([cash_store_name, *(asset_classes or {})])
    params = TaxManagerParameters(
        cash_store_name=cash_store_name,
        sparerpauschbetrag=sparerpauschbetrag,
        basiszins=basiszins,
        withholding_tax_rate=withholding_tax_rate,
        soli_rate=soli_rate,
        church_tax_rate=church_tax_rate,
        tariff=tariff or IncomeTaxTariff(),
        kvdr_rate=kvdr_rate,
        pv_rate=pv_rate,
        retirement_step=retirement_step,
        start_year=start_year,
        asset_classes=asset_classes or {},
    )

    # Split into two effects with an explicit execution order (rather than
    # one "tax manager" effect) because the two halves need opposite
    # positions relative to the Cash-Bucket-Manager (order=0, see
    # portfolio.py): pension tax must be deducted before the bucket sweeps
    # cash to its target, or the cash balance always lands short by the tax
    # amount; capital gains tax must run after, since it taxes
    # `store.withdrawn_lots_this_step`, which is only populated once the
    # bucket manager has actually sold something in this step.
    plan.effects.append(
        ComputedEffect(
            name="Pension Income Tax Manager",
            function_name="pension_income_tax_manager",
            order=-10,
            parameters=params.model_dump(),
            description=description,
        )
    )
    plan.effects.append(
        ComputedEffect(
            name="Capital Gains Tax Manager",
            function_name="capital_gains_tax_manager",
            order=10,
            parameters=params.model_dump(),
            description=description,
        )
    )
