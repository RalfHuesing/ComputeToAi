"""German taxation system (Abgeltungsteuer, Sparerpauschbetrag, Vorabpauschale, rent tax).

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/04-Feature-Finanzen-Methodik.md.
"""

from typing import Any

from compute_to_ai.engine.effect import ComputedEffect, register_computed_effect
from compute_to_ai.engine.plan import Plan


def calculate_german_income_tax(zv: float, gfb: float = 11784.0) -> float:
    """Calculate the progressive German income tax according to § 32a EStG for 2024."""
    if zv <= gfb:
        return 0.0

    if zv <= 17005.0:
        y = (zv - gfb) / 10000.0
        return (995.21 * y + 1400.0) * y

    if zv <= 66760.0:
        z = (zv - 17005.0) / 10000.0
        return ((208.85 * z + 2397.0) * z) + 951.64

    if zv <= 277825.0:
        return 0.42 * zv - 10602.13

    return 0.45 * zv - 18936.88


def _apply_pension_taxation(
    balances: dict[str, float],
    step: int,
    plan: Plan,
    cash_store: str,
    parameters: dict[str, Any],
    active_phase: str | None,
) -> None:
    """Calculate and deduct progressive tax and KVdR/PV contributions from pension income."""
    retirement_step = int(parameters.get("retirement_step", 47))
    start_year = int(parameters.get("start_year", 2026))
    gfb = float(parameters.get("gfb", 11784.0))
    kvdr_rate = float(parameters.get("kvdr_rate", 0.0875))
    pv_rate = float(parameters.get("pv_rate", 0.042))

    is_rente = active_phase is not None and "rente" in active_phase.lower()
    if not (is_rente or step >= retirement_step):
        return

    # Sum rent income (positive cashflows from Phase 1)
    rent_income = 0.0
    for effect in plan.effects:
        if (
            effect.is_active(step, active_phase)
            and getattr(effect, "store_name", None) == cash_store
        ):
            amount = getattr(effect, "amount_per_step", 0.0)
            rate = getattr(effect, "growth_rate", 0.0)
            val = amount * ((1.0 + rate) ** step)
            if val > 0.0:
                rent_income += val

    if rent_income > 0.0:
        # Insurance contributions
        insurance_premium = rent_income * (kvdr_rate + pv_rate)
        balances[cash_store] = balances.get(cash_store, 0.0) - insurance_premium

        # Taxable share based on retirement year
        retirement_year = start_year + retirement_step
        taxable_share = min(1.0, 0.84 + 0.005 * (retirement_year - 2026))
        rent_taxable = rent_income * taxable_share

        # Taxable income (Einkommensteuer-Bemessungsgrundlage)
        zv = max(0.0, rent_taxable - gfb - insurance_premium)
        rent_tax = calculate_german_income_tax(zv, gfb)
        balances[cash_store] = balances.get(cash_store, 0.0) - rent_tax


def _calculate_sales_taxable_gains(
    balances: dict[str, float], plan: Plan, asset_classes: dict[str, Any]
) -> float:
    """Compute total taxable gains from sales from withdrawn lots during this step."""
    gains_from_sales = 0.0
    for name, ac_cfg in asset_classes.items():
        if name not in balances:
            continue
        store = plan.store(name)
        partial_exemption = float(ac_cfg.get("partial_exemption_rate", 0.0))
        for lot in store.withdrawn_lots_this_step:
            is_pre_2009 = lot.created_step < 0 or lot.rule_version == "pre_2009"
            if not is_pre_2009:
                raw_gain = lot.quantity - lot.cost_basis
                taxable_gain = max(0.0, raw_gain - lot.taxed_vorabpauschale)
                gains_from_sales += taxable_gain * (1.0 - partial_exemption)
    return gains_from_sales


def _calculate_vorabpauschale_taxable(
    balances: dict[str, float], plan: Plan, asset_classes: dict[str, Any], basiszins: float
) -> float:
    """Calculate the taxable Vorabpauschale on accumulating lots at the end of the year."""
    vorab_taxable_total = 0.0
    for name, ac_cfg in asset_classes.items():
        if name not in balances:
            continue
        is_acc = ac_cfg.get("is_accumulating", False)
        if not is_acc:
            continue

        store = plan.store(name)
        growth_rate = float(ac_cfg.get("growth_rate", 0.0))
        partial_exemption = float(ac_cfg.get("partial_exemption_rate", 0.0))

        # Calculate Vorabpauschale on remaining lots at the end of the year
        for lot in store.lots:
            growth_factor = 1.0 + growth_rate
            q_start = lot.quantity / growth_factor
            actual_growth = lot.quantity - q_start
            potential_vorab = q_start * basiszins * 0.7
            vorab = min(potential_vorab, max(0.0, actual_growth))

            vorab_taxable_total += vorab * (1.0 - partial_exemption)
            # Add to taxed_vorabpauschale to avoid double taxation on sale
            lot.taxed_vorabpauschale += vorab
    return vorab_taxable_total


def _apply_capital_gains_taxation(
    balances: dict[str, float],
    plan: Plan,
    cash_store: str,
    parameters: dict[str, Any],
) -> None:
    """Calculate and deduct capital gains tax (withholding tax, allowance, Vorabpauschale)."""
    sparerpauschbetrag = float(parameters.get("sparerpauschbetrag", 1000.0))
    basiszins = float(parameters.get("basiszins", 0.032))
    withholding_tax_rate = float(parameters.get("withholding_tax_rate", 0.25))
    soli_rate = float(parameters.get("soli_rate", 0.055))
    church_tax_rate = float(parameters.get("church_tax_rate", 0.0))
    asset_classes = parameters.get("asset_classes", {})

    gains_from_sales = _calculate_sales_taxable_gains(balances, plan, asset_classes)
    vorab_taxable_total = _calculate_vorabpauschale_taxable(
        balances, plan, asset_classes, basiszins
    )

    # 4. Abgeltungsteuer-Abrechnung
    total_cap_gains = gains_from_sales + vorab_taxable_total
    if total_cap_gains > sparerpauschbetrag:
        excess = total_cap_gains - sparerpauschbetrag
        eff_rate = withholding_tax_rate * (1.0 + soli_rate + church_tax_rate)
        cap_gains_tax = excess * eff_rate
        balances[cash_store] = balances.get(cash_store, 0.0) - cap_gains_tax


@register_computed_effect("tax_manager")
def tax_manager_func(  # pyright: ignore[reportUnusedFunction]
    balances: dict[str, float], step: int, parameters: dict[str, Any], plan: Plan
) -> None:
    """Computed effect implementing capital gains and progressive pension income taxation."""
    cash_store = str(parameters.get("cash_store_name", "cash"))
    active_phase = plan.get_active_phase_name(step)

    # 1. Progressive Renten-Besteuerung und KVdR/PV
    _apply_pension_taxation(balances, step, plan, cash_store, parameters, active_phase)

    # 2. Kapitalertragssteuer & Vorabpauschale
    _apply_capital_gains_taxation(balances, plan, cash_store, parameters)


def add_tax_manager(
    plan: Plan,
    cash_store_name: str = "cash",
    sparerpauschbetrag: float = 1000.0,
    basiszins: float = 0.032,
    withholding_tax_rate: float = 0.25,
    soli_rate: float = 0.055,
    church_tax_rate: float = 0.0,
    gfb: float = 11784.0,
    kvdr_rate: float = 0.0875,
    pv_rate: float = 0.042,
    retirement_step: int = 47,
    start_year: int = 2026,
    asset_classes: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Add a computed tax manager to the plan."""
    effect = ComputedEffect(
        name="Tax Manager",
        function_name="tax_manager",
        parameters={
            "cash_store_name": cash_store_name,
            "sparerpauschbetrag": sparerpauschbetrag,
            "basiszins": basiszins,
            "withholding_tax_rate": withholding_tax_rate,
            "soli_rate": soli_rate,
            "church_tax_rate": church_tax_rate,
            "gfb": gfb,
            "kvdr_rate": kvdr_rate,
            "pv_rate": pv_rate,
            "retirement_step": retirement_step,
            "start_year": start_year,
            "asset_classes": asset_classes or {},
        },
    )
    plan.effects.append(effect)
