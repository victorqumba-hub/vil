from pydantic import BaseModel, Field

class PipelineRunRequest(BaseModel):
    symbols: list[str] | None = None
    timeframe: str = "H1"
    top_n: int = 6
    min_score: float = 40.0
