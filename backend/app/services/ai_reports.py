"""AI Report Generator — Mistral API integration.

Generates institutional-quality analysis reports for trading signals.
Falls back to template-based mock reports when API key is not configured.
"""

import httpx
from app.config import settings


SYSTEM_PROMPT = """You are an institutional-grade trading analyst for Victor Institutional Logic (VIL).
Generate concise, professional analysis reports for trading signals.

Your reports must include:
1. **Summary** — One-paragraph overview of the signal and market context.
2. **Rationale** — Technical and fundamental justification.
3. **Risk Assessment** — Position sizing context, key levels, and risk factors.

Write in a confident, analytical tone suitable for professional traders.
Keep each section to 2-3 sentences maximum."""


async def generate_ai_report(signal: dict) -> dict:
    """
    Generate AI analysis report for a signal.

    If MISTRAL_API_KEY is not set, returns a template-based mock report.
    """
    if not settings.MISTRAL_API_KEY:
        return _mock_report(signal)

    try:
        return await _mistral_report(signal)
    except Exception as e:
        print(f"[AI Reports] Mistral API error: {e}")
        return _mock_report(signal)


async def _mistral_report(signal: dict) -> dict:
    """Call Mistral API to generate the report."""
    prompt = f"""Analyze this trading signal and generate a report:

Symbol: {signal.get('symbol')}
Direction: {signal.get('direction')}
Entry: {signal.get('entry_price')}
Stop Loss: {signal.get('stop_loss')}
Take Profit: {signal.get('take_profit')}
Risk/Reward: {signal.get('risk_reward')}
Score: {signal.get('score')}/100
Regime: {signal.get('regime_detail', {}).get('regime')} (Conf: {signal.get('regime_detail', {}).get('confidence')}%)
Structure: {signal.get('structure_detail', {}).get('reason')} (Last Break: {signal.get('structure_detail', {}).get('last_break')})
Liquidity: {signal.get('liquidity_detail', {}).get('vol_state')} (Sweep: {signal.get('liquidity_detail', {}).get('sweep')})
ATR: {signal.get('technicals', {}).get('atr')}
ADX: {signal.get('technicals', {}).get('adx')}
RSI: {signal.get('technicals', {}).get('rsi')}

Provide: Summary, Rationale (mentioning Structure & Liquidity), Risk Assessment."""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.MISTRAL_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 500,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Parse sections
        sections = _parse_sections(content)
        return {
            "summary": sections.get("summary", content[:200]),
            "rationale": sections.get("rationale", ""),
            "risk_assessment": sections.get("risk_assessment", ""),
            "model": settings.MISTRAL_MODEL,
            "source": "mistral",
        }


def _parse_sections(text: str) -> dict:
    """Parse AI output into sections."""
    sections = {}
    current = "summary"
    lines = []

    for line in text.split("\n"):
        lower = line.lower().strip()
        if "rationale" in lower and ("**" in lower or "#" in lower or lower.startswith("rationale")):
            sections[current] = " ".join(lines).strip()
            current = "rationale"
            lines = []
        elif "risk" in lower and ("**" in lower or "#" in lower or lower.startswith("risk")):
            sections[current] = " ".join(lines).strip()
            current = "risk_assessment"
            lines = []
        elif "summary" in lower and ("**" in lower or "#" in lower):
            current = "summary"
            lines = []
        else:
            cleaned = line.strip().strip("*#").strip()
            if cleaned:
                lines.append(cleaned)

    sections[current] = " ".join(lines).strip()
    return sections


def _mock_report(signal: dict) -> dict:
    """Generate a template-based mock report."""
    sym = signal.get("symbol", "?")
    direction = signal.get("direction", "?")
    score = signal.get("score", 0)
    regime = signal.get("regime", "UNKNOWN")
    rr = signal.get("risk_reward", 0)
    entry = signal.get("entry_price", 0)
    sl = signal.get("stop_loss", 0)
    tp = signal.get("take_profit", 0)

    regime_desc = {
        "TRENDING": "trending market conditions with strong directional momentum",
        "RANGING": "range-bound conditions with mean-reversion opportunities",
        "HIGH_VOLATILITY": "elevated volatility requiring wider stops and careful sizing",
        "LOW_ACTIVITY": "low activity environment with limited opportunity",
    }.get(regime, "current market conditions")

    summary = (
        f"VIL analysis recommends a {direction} position on {sym} with a quality score of {score}/100. "
        f"The signal was generated under {regime_desc}. "
        f"Entry at {entry}, targeting {tp} with stop at {sl}."
    )

    struct = signal.get("structure_detail", {})
    liq = signal.get("liquidity_detail", {})
    
    rationale = (
        f"Structure analysis ({struct.get('confidence', 0)}% conf) indicates {struct.get('reason', 'neutral bias')}. "
        f"Liquidity state is {liq.get('vol_state', 'NORMAL')}{' with sweep detected' if liq.get('sweep') else ''}. "
        f"Multi-timeframe analysis shows confluence across H1/H4 with "
        f"{'bullish' if direction == 'BUY' else 'bearish'} pressure. "
        f"Technical indicators align with the {regime.lower().replace('_', ' ')} classification."
    )

    risk_assessment = (
        f"Risk/Reward ratio: {rr}:1. "
        f"Position size calibrated to institutional risk parameters. "
        f"{'Favorable' if rr >= 1.5 else 'Acceptable'} setup for {regime.lower().replace('_', ' ')} regime."
    )

    return {
        "summary": summary,
        "rationale": rationale,
        "risk_assessment": risk_assessment,
        "model": "template",
        "source": "mock",
    }
