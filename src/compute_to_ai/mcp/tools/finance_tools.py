"""Finance tools registration backward-compatibility wrapper.

See Docs/02-Architektur-und-MCP.md for the `finance_` tool-name prefix.
Delegates to `compute_to_ai.mcp.tools.finance.register_finance_tools`.
"""

from compute_to_ai.mcp.tools.finance import register_finance_tools

__all__ = ["register_finance_tools"]
