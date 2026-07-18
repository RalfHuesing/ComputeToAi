"""Finance feature module exports.

See Docs/03-Feature-Finanzen-Domaenenmodell.md and Docs/11-Code-Standards-und-Projektstruktur.md.
"""

from compute_to_ai.features.finance.cashflow import (
    add_expense,
    add_fixed_acquisition,
    add_flexible_acquisition,
    add_income_stream,
)
from compute_to_ai.features.finance.liability import add_liability
from compute_to_ai.features.finance.pension import add_statutory_pension
from compute_to_ai.features.finance.phases import build_standard_life_phases
from compute_to_ai.features.finance.portfolio import (
    add_asset_class,
    add_cash_bucket,
    add_portfolio_rebalancing,
    set_correlation_matrix,
)
from compute_to_ai.features.finance.tax import add_tax_manager

__all__ = [
    "add_asset_class",
    "add_cash_bucket",
    "add_expense",
    "add_fixed_acquisition",
    "add_flexible_acquisition",
    "add_income_stream",
    "add_liability",
    "add_portfolio_rebalancing",
    "add_statutory_pension",
    "add_tax_manager",
    "build_standard_life_phases",
    "set_correlation_matrix",
]
