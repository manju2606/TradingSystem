import json

from openai import AsyncOpenAI

from backend.api.config import settings

_client = AsyncOpenAI(api_key=settings.openai_api_key)


async def journal_agent_node(state: dict) -> dict:
    prompt = f"""
You are a trade journal agent. Write a concise trade journal entry for this cycle.

Symbol: {state['symbol']} | Timeframe: {state['timeframe']}
Market analysis: {json.dumps(state['market_analysis'])}
Signal: {json.dumps(state['signal'])}
Risk assessment: {json.dumps(state['risk_assessment'])}
Execution: {json.dumps(state['execution_result'])}

Write: what happened, why the signal was taken/rejected, lessons learned (2-3 sentences max).
"""
    response = await _client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
    )
    entry = response.choices[0].message.content
    return {**state, "journal_entry": entry}
