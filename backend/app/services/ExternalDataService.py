"""External Data Service — Fetches macro news and economic indicators."""

import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ExternalDataService:
    def __init__(self):
        # In a production env, these would use real API keys for AlphaVantage, Bloomberg, etc.
        self.mock_mode = True

    async def get_news_catalysts(self, symbol: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Fetch news events that may have acted as catalysts for a signal."""
        if self.mock_mode:
            # Mock news alignment logic
            return [
                {
                    "title": f"Volatility Spike in {symbol} following FOMC minutes",
                    "impact": "HIGH",
                    "category": "MACRO",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        return []

    async def get_calendar_events(self, currencies: List[str], start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Fetch economic calendar events for the relevant currencies."""
        if self.mock_mode:
            return [
                {
                    "event": "Non-Farm Payrolls",
                    "impact": "HIGH",
                    "currency": "USD",
                    "actual": "225K",
                    "forecast": "180K",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        return []

external_data_service = ExternalDataService()
