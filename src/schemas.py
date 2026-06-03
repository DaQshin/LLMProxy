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
