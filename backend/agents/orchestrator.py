from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from backend.agents.execution_agent import execution_agent_node
from backend.agents.journal_agent import journal_agent_node
from backend.agents.market_analyst import market_analyst_node
from backend.agents.risk_agent import risk_agent_node
from backend.agents.signal_validator import signal_validator_node


class TradingState(TypedDict):
    symbol: str
    timeframe: str
    market_analysis: dict
    signal: dict
    risk_assessment: dict
    execution_result: dict
    journal_entry: str
    messages: list[dict]


def _route_after_validation(state: TradingState) -> str:
    if state["signal"].get("approved"):
        return "risk_agent"
    return END


def _route_after_risk(state: TradingState) -> str:
    if state["risk_assessment"].get("approved"):
        return "execution_agent"
    return END


def build_graph() -> Any:
    g = StateGraph(TradingState)

    g.add_node("market_analyst", market_analyst_node)
    g.add_node("signal_validator", signal_validator_node)
    g.add_node("risk_agent", risk_agent_node)
    g.add_node("execution_agent", execution_agent_node)
    g.add_node("journal_agent", journal_agent_node)

    g.set_entry_point("market_analyst")
    g.add_edge("market_analyst", "signal_validator")
    g.add_conditional_edges("signal_validator", _route_after_validation)
    g.add_conditional_edges("risk_agent", _route_after_risk)
    g.add_edge("execution_agent", "journal_agent")
    g.add_edge("journal_agent", END)

    return g.compile()


_graph = build_graph()


async def run_trading_cycle(symbol: str, timeframe: str) -> TradingState:
    initial_state: TradingState = {
        "symbol": symbol,
        "timeframe": timeframe,
        "market_analysis": {},
        "signal": {},
        "risk_assessment": {},
        "execution_result": {},
        "journal_entry": "",
        "messages": [],
    }
    return await _graph.ainvoke(initial_state)
