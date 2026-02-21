import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class MLClient:
    """Institutional client for high-speed ML inference."""
    
    def __init__(self, base_url: str = settings.ML_SERVICE_URL):
        self.base_url = base_url
        self.timeout = httpx.Timeout(2.0, connect=1.0) # Conservative timeout for Dev
        
    async def get_success_probability(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calls the ML Service to predict signal success probability.
        """
        url = f"{self.base_url}/predict/success"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=features)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logger.warning(f"[MLClient] Service error {resp.status_code}: {resp.text}")
                    return None
        except httpx.TimeoutException:
            logger.error(f"[MLClient] Timeout calling ML service at {url}")
            return None
        except Exception as e:
            logger.error(f"[MLClient] Unexpected error calling ML service: {e}")
            return None

    async def log_outcome(self, signal_id: str, outcome: str, r_multiple: float = 0.0) -> bool:
        """
        Logs a trade outcome to the ML Feature Store for closed-loop learning.
        outcome: "SUCCESS" or "FAILED"
        """
        url = f"{self.base_url}/dataset/outcome"
        payload = {
            "signalId": str(signal_id),
            "outcome": outcome,
            "rMultiple": r_multiple
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"[MLClient] Error logging outcome to ML service: {e}")
            return False

    async def get_failure_classification(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calls the ML Service to classify potential failure mode.
        """
        url = f"{self.base_url}/predict/failure"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=features)
                if resp.status_code == 200:
                    return resp.json()
                return None
        except Exception as e:
            logger.error(f"[MLClient] Error calling ML failure classification: {e}")
            return None

# Singleton instance
ml_client = MLClient()
