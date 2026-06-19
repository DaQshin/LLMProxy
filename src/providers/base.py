from abc import ABC, abstractmethod
from pydantic import BaseModel

class ProviderResponse(BaseModel):
    text: str
    input_tokens: int
    output_tokens: int
    model: str


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, prompt: str, model: str, max_tokens: int) -> ProviderResponse:
        ...
