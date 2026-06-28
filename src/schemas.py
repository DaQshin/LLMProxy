from pydantic import BaseModel, Field

class Request(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    model: str = Field(default="claude-sonnet-4-6")
    max_tokens: int = Field(default=512, ge=1, le=4096)


class Response(BaseModel):
    response: str
    model: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_usd: float

class ErrorResponse(BaseModel):
    message: str

class ProviderStats(BaseModel):
    calls: int
    avg_input_tokens: float
    avg_output_tokens: float
    avg_latency_ms: float
    avg_cost_usd: float

class StatsResponse(BaseModel):
    total_calls: int
    cache_hit_rate: float
    avg_latency_ms: float
    total_cost_usd: float
    by_model: dict[str, ProviderStats]

