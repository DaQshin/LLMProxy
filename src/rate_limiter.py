import time 
import asyncio

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.tokens, self.rate * elapsed + self.tokens)
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            return False
        
