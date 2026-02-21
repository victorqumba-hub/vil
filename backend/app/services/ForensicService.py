"""Forensic Service — Orchestrates signal analysis and batch reporting with ML Service."""

import logging
import httpx
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Signal, LifecycleStatus

logger = logging.getLogger(__name__)

class ForensicService:
    def __init__(self):
        self.ml_service_url = "http://localhost:8001"

    async def trigger_signal_analysis(self, signal_id: str):
        """Notifies ML Service to perform forensic analysis on a terminal signal."""
        logger.info(f"[ForensicService] Triggering analysis for signal {signal_id}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.ml_service_url}/forensics/analyze/{signal_id}")
                if resp.status_code == 200:
                    logger.info(f"[ForensicService] Analysis completed for {signal_id}")
                    # After analysis, check if we should trigger a batch report
                    return True
                else:
                    logger.warning(f"[ForensicService] ML Service returned {resp.status_code} for {signal_id}")
        except Exception as e:
            logger.error(f"[ForensicService] Failed to contact ML Service: {e}")
        return False

    async def check_and_trigger_batch_report(self, db: AsyncSession):
        """Checks if 50+ analyzed signals exist and triggers a batch report."""
        # Check count of analyzed signals since last report
        # For simplicity, we check total analyzed vs total reports or just raw count
        from sqlalchemy import text
        query = text("SELECT COUNT(*) FROM signal_forensic_analysis")
        result = await db.execute(query)
        count = result.scalar()
        
        # Also check when the last report was generated
        report_query = text("SELECT COUNT(*) FROM signal_intelligence_reports")
        report_count_res = await db.execute(report_query)
        report_count = report_count_res.scalar()
        
        # Logic: If unanalyzed signals > 50 (simplification: total > 50 * report_count)
        if count >= 50 and (report_count == 0 or count >= 50 * (report_count + 1)):
            logger.info(f"[ForensicService] Triggering batch report (Analyzed: {count}, Reports: {report_count})")
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(f"{self.ml_service_url}/forensics/report")
                    if resp.status_code == 200:
                        logger.info("[ForensicService] Batch report generated successfully.")
                        return True
            except Exception as e:
                logger.error(f"[ForensicService] Failed to trigger batch report: {e}")
        
        return False

forensic_service = ForensicService()
