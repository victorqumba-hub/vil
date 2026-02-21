from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

class PipelineStatus(BaseModel):
    last_run_time: Optional[str] = None
    status: str = "idle"  # idle, running, success, error
    last_error: Optional[str] = None
    last_success_time: Optional[str] = None
    last_failure_time: Optional[str] = None
    processed_symbols: List[str] = []
    message: str = "Waiting for first run..."

class PipelineMonitor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PipelineMonitor, cls).__new__(cls)
            cls._instance.state = PipelineStatus()
        return cls._instance

    def update_status(self, **kwargs):
        current_state = self.state.dict()
        current_state.update(kwargs)
        self.state = PipelineStatus(**current_state)

    def get_status(self) -> PipelineStatus:
        return self.state

monitor = PipelineMonitor()
