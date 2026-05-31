from pydantic import BaseModel

class Request(BaseModel):
    prompt: str
    model: str = "claude-3-5-haiku-20241022"
    max_tokens: int = 512


class Response(BaseModel):
    response: str
    model: str
    latency_ms: float
