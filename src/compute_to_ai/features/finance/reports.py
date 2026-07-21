"""Reports and evaluations: Asset Allocation Drift, Sale Tax Estimator, Plan vs. Actual Comparison.

See Docs/04-Feature-Finanzen-Methodik.md for details.
"""

from typing import Any

from compute_to_ai.engine.effect import ComputedEffect, CorrelatedReturnEffect
from compute_to_ai.engine.plan import Plan
from compute_to_ai.engine.result import PathAuditResult
from compute_to_ai.engine.simulation import run_path_audit
from compute_to_ai.features.finance.path_audit import _liability_store_names, get_percentile_curves
from compute_to_ai.features.finance.position import PositionRegistry


def get_partial_exemption_rate(asset_type: str) -> float:
    """Return partial exemption rate (Teilfreistellung) under InvStG for asset_type."""
    mapping = {
        "equity_fund": 0.30,
        "mixed_fund": 0.15,
        "real_estate_fund": 0.60,
        "bond_fund": 0.0,
        "stock": 0.0,
    }
    return mapping.get(asset_type, 0.0)


def store_exists(plan: Plan, store_name: str) -> bool:
    """Helper to check if store exists in plan."""
    return any(st.name == store_name for st in plan.stores)


def _analyze_lots(store: Any) -> dict[str, float]:
    """Analyze lots for a store to compute cost basis and gains (pre-2009 vs regular)."""
    if not store.lots:
        return {
            "cost_basis": store.balance,
            "unrealized_gain": 0.0,
            "unrealized_gain_percent": 0.0,
            "pre_2009_cost_basis": 0.0,
            "pre_2009_unrealized_gain": 0.0,
            "regular_cost_basis": store.balance,
            "regular_unrealized_gain": 0.0,
        }

    pre_2009_cost = 0.0
    pre_2009_gain = 0.0
    regular_cost = 0.0
    regular_gain = 0.0

    for lot in store.lots:
        gain = lot.quantity - lot.cost_basis
        if lot.rule_version in ("pre_2009", "2008_or_earlier"):
            pre_2009_cost += lot.cost_basis
            pre_2009_gain += gain
        else:
            regular_cost += lot.cost_basis
            regular_gain += gain

    total_cost = pre_2009_cost + regular_cost
    total_gain = pre_2009_gain + regular_gain
    gain_pct = (total_gain / total_cost * 100.0) if total_cost > 0.0 else 0.0

    return {
        "cost_basis": total_cost,
        "unrealized_gain": total_gain,
        "unrealized_gain_percent": gain_pct,
        "pre_2009_cost_basis": pre_2009_cost,
        "pre_2009_unrealized_gain": pre_2009_gain,
        "regular_cost_basis": regular_cost,
        "regular_unrealized_gain": regular_gain,
    }


def _get_target_weights(plan: Plan) -> dict[str, float]:
    for effect in plan.effects:
        if isinstance(effect, ComputedEffect) and effect.function_name == "portfolio_rebalancing":
            return effect.parameters.get("weights", {})
    return {}


def _collect_asset_class_stores(plan: Plan) -> tuple[dict[str, list[str]], set[str]]:
    asset_class_stores: dict[str, list[str]] = {}
    invested_stores: set[str] = set()
    for effect in plan.effects:
        if isinstance(effect, CorrelatedReturnEffect):
            asset_class_stores[effect.name] = list(effect.store_names)
            invested_stores.update(effect.store_names)

    liability_stores = _liability_store_names(plan)
    if not asset_class_stores:
        for store in plan.stores:
            if store.name not in liability_stores:
                asset_class_stores[store.name] = [store.name]
                invested_stores.add(store.name)

    return asset_class_stores, invested_stores


def _build_pos_details(
    plan: Plan, s_names: list[str], registry: PositionRegistry
) -> list[dict[str, Any]]:
    pos_details: list[dict[str, Any]] = []
    for s_name in s_names:
        if not store_exists(plan, s_name):
            continue
        st = plan.store(s_name)
        meta = registry.positions.get(s_name)
        asset_type = meta.asset_type if meta else "equity_fund"
        pos_details.append(
            {
                "store_name": s_name,
                "asset_type": asset_type,
                "balance": st.balance,
                **_analyze_lots(st),
            }
        )
    return pos_details


def get_asset_allocation_report(
    plan: Plan,
    position_registry: PositionRegistry | None = None,
    metadata_store: PositionRegistry | None = None,
) -> dict[str, Any]:
    """Computes target vs actual asset allocation, drift, and unrealized gains breakdown."""
    registry = position_registry or metadata_store or PositionRegistry()
    target_weights = _get_target_weights(plan)
    asset_class_stores, invested_stores = _collect_asset_class_stores(plan)

    total_portfolio_value = sum(
        plan.store(s_name).balance for s_name in invested_stores if store_exists(plan, s_name)
    )

    asset_classes_report: list[dict[str, Any]] = []
    for ac_name, s_names in asset_class_stores.items():
        ac_value = sum(
            plan.store(s_name).balance for s_name in s_names if store_exists(plan, s_name)
        )
        target_w = target_weights.get(ac_name, 0.0)
        if target_w == 0.0 and len(s_names) == 1:
            target_w = target_weights.get(s_names[0], 0.0)

        actual_w = (ac_value / total_portfolio_value) if total_portfolio_value > 0.0 else 0.0
        drift = actual_w - target_w
        pos_details = _build_pos_details(plan, s_names, registry)

        asset_classes_report.append(
            {
                "asset_class": ac_name,
                "target_weight": target_w,
                "actual_value": ac_value,
                "actual_weight": actual_w,
                "drift": drift,
                "positions": pos_details,
            }
        )

    liability_stores = _liability_store_names(plan)
    all_positions: list[dict[str, Any]] = []
    for st in plan.stores:
        if st.name in liability_stores:
            continue
        meta = registry.positions.get(st.name)
        asset_type = meta.asset_type if meta else "equity_fund"
        all_positions.append(
            {
                "store_name": st.name,
                "asset_type": asset_type,
                "balance": st.balance,
                **_analyze_lots(st),
            }
        )

    return {
        "total_portfolio_value": total_portfolio_value,
        "asset_classes": asset_classes_report,
        "positions": all_positions,
    }


def _determine_sale_amount(
    st_balance: float,
    total_shares: float | None,
    shares_to_sell: float | None,
    amount_to_sell: float | None,
    sell_all: bool,
) -> tuple[float, float | None]:
    if sell_all:
        return st_balance, total_shares
    if shares_to_sell is not None:
        if shares_to_sell <= 0.0:
            msg = "shares_to_sell must be positive"
            raise ValueError(msg)
        if total_shares is not None and shares_to_sell > total_shares:
            msg = (
                f"Requested selling {shares_to_sell} shares, "
                f"but position only has {total_shares} shares"
            )
            raise ValueError(msg)
        if total_shares and total_shares > 0.0:
            return (shares_to_sell / total_shares) * st_balance, shares_to_sell
        return st_balance, shares_to_sell
    if amount_to_sell is not None:
        if amount_to_sell <= 0.0:
            msg = "amount_to_sell must be positive"
            raise ValueError(msg)
        if amount_to_sell > st_balance + 1e-6:
            msg = (
                f"Requested selling {amount_to_sell} EUR, "
                f"but position balance is only {st_balance} EUR"
            )
            raise ValueError(msg)
        sh_sold = (
            (amount_to_sell / st_balance * total_shares)
            if (total_shares and st_balance > 0.0)
            else None
        )
        return amount_to_sell, sh_sold
    msg = "Must specify one of sell_all=True, shares_to_sell, or amount_to_sell"
    raise ValueError(msg)


def estimate_sale_tax(
    plan: Plan,
    store_name: str,
    position_registry: PositionRegistry | None = None,
    metadata_store: PositionRegistry | None = None,
    shares_to_sell: float | None = None,
    amount_to_sell: float | None = None,
    sell_all: bool = False,
    remaining_savers_allowance: float = 1000.0,
    church_tax_rate: float = 0.0,
) -> dict[str, Any]:
    """Estimates taxes for a hypothetical sale of shares or EUR amount of a position."""
    registry = position_registry or metadata_store or PositionRegistry()

    if not store_exists(plan, store_name):
        msg = f"Store {store_name!r} not found in plan"
        raise ValueError(msg)

    st = plan.store(store_name)
    meta = registry.positions.get(store_name)
    asset_type = meta.asset_type if meta else "equity_fund"
    total_shares = meta.shares if meta else None

    gross_sale_amount, shares_sold = _determine_sale_amount(
        st.balance, total_shares, shares_to_sell, amount_to_sell, sell_all
    )

    p_rate = get_partial_exemption_rate(asset_type)
    if gross_sale_amount <= 0.0:
        return _empty_tax_result(store_name, shares_sold, p_rate)

    total_gross_gain, pre_2009_exempt, taxable_before_ex = _consume_lots_for_tax(
        st, gross_sale_amount
    )

    p_amount = taxable_before_ex * p_rate
    taxable_after_ex = max(0.0, taxable_before_ex - p_amount)
    savers_used = min(taxable_after_ex, max(0.0, remaining_savers_allowance))
    net_taxable = max(0.0, taxable_after_ex - savers_used)

    abgeltungtax = net_taxable * 0.25
    soli = abgeltungtax * 0.055
    church_tax = abgeltungtax * church_tax_rate
    total_tax = abgeltungtax + soli + church_tax

    return {
        "store_name": store_name,
        "gross_sale_amount": gross_sale_amount,
        "shares_sold": shares_sold,
        "gross_gain": total_gross_gain,
        "pre_2009_exempt_gain": pre_2009_exempt,
        "taxable_gain_before_exemption": taxable_before_ex,
        "partial_exemption_rate": p_rate,
        "partial_exemption_amount": p_amount,
        "taxable_gain_after_exemption": taxable_after_ex,
        "savers_allowance_used": savers_used,
        "net_taxable_gain": net_taxable,
        "abgeltungsteuer": abgeltungtax,
        "soli": soli,
        "church_tax": church_tax,
        "total_tax": total_tax,
        "net_proceeds": gross_sale_amount - total_tax,
        "effective_tax_rate": (total_tax / gross_sale_amount) if gross_sale_amount > 0.0 else 0.0,
    }


def _empty_tax_result(store_name: str, shares_sold: float | None, p_rate: float) -> dict[str, Any]:
    return {
        "store_name": store_name,
        "gross_sale_amount": 0.0,
        "shares_sold": shares_sold,
        "gross_gain": 0.0,
        "pre_2009_exempt_gain": 0.0,
        "taxable_gain_before_exemption": 0.0,
        "partial_exemption_rate": p_rate,
        "partial_exemption_amount": 0.0,
        "taxable_gain_after_exemption": 0.0,
        "savers_allowance_used": 0.0,
        "net_taxable_gain": 0.0,
        "abgeltungsteuer": 0.0,
        "soli": 0.0,
        "church_tax": 0.0,
        "total_tax": 0.0,
        "net_proceeds": 0.0,
        "effective_tax_rate": 0.0,
    }


def _consume_lots_for_tax(st: Any, gross_sale_amount: float) -> tuple[float, float, float]:
    if not st.lots:
        return 0.0, 0.0, 0.0

    remaining = gross_sale_amount
    total_gross_gain = 0.0
    pre_2009_exempt = 0.0
    taxable_before_ex = 0.0

    for lot in st.lots:
        if remaining <= 0:
            break
        consumed_qty = min(lot.quantity, remaining)
        fraction = consumed_qty / lot.quantity if lot.quantity > 0 else 1.0
        consumed_cost = lot.cost_basis * fraction
        lot_gain = consumed_qty - consumed_cost

        total_gross_gain += lot_gain
        if lot.rule_version in ("pre_2009", "2008_or_earlier"):
            pre_2009_exempt += max(0.0, lot_gain)
        else:
            taxable_before_ex += max(0.0, lot_gain)

        remaining -= consumed_qty

    return total_gross_gain, pre_2009_exempt, taxable_before_ex


def compare_plan_actuals(
    plan: Plan,
    audit_result: PathAuditResult | None = None,
    current_step: int = 0,
) -> dict[str, Any]:
    """Compares current total net worth against Monte Carlo percentile curves (p10, p50, p90)."""
    if audit_result is None:
        audit_result = run_path_audit(plan, num_runs=100, percentiles=(10, 50, 90))

    curves = get_percentile_curves(plan, audit_result)
    p50_curve = curves.get("p50") or curves.get("deterministic") or []
    if not p50_curve:
        msg = "No percentile curves available in audit_result"
        raise ValueError(msg)

    if current_step < 0 or current_step >= len(p50_curve):
        msg = (
            f"current_step {current_step} is out of bounds for simulation horizon "
            f"(0-{len(p50_curve) - 1})"
        )
        raise ValueError(msg)

    p10_curve = curves.get("p10") or p50_curve
    p90_curve = curves.get("p90") or p50_curve

    liability_stores = _liability_store_names(plan)
    total_net_worth = sum(
        st.balance if st.name not in liability_stores else -st.balance for st in plan.stores
    )

    p10_val = p10_curve[current_step]["total_net"]
    p50_val = p50_curve[current_step]["total_net"]
    p90_val = p90_curve[current_step]["total_net"]

    if total_net_worth < p10_val:
        status = "BELOW_P10"
    elif total_net_worth <= p50_val:
        status = "BETWEEN_P10_AND_P50"
    elif total_net_worth <= p90_val:
        status = "BETWEEN_P50_AND_P90"
    else:
        status = "ABOVE_P90"

    delta_eur = total_net_worth - p50_val
    delta_pct = (delta_eur / p50_val * 100.0) if p50_val != 0.0 else 0.0

    return {
        "current_step": current_step,
        "current_net_worth": total_net_worth,
        "status": status,
        "p10_net_worth": p10_val,
        "p50_net_worth": p50_val,
        "p90_net_worth": p90_val,
        "delta_to_p50_eur": delta_eur,
        "delta_to_p50_percent": delta_pct,
    }
