import time
import httpx
from contextlib import asynccontextmanager
from .schemas import Request, Response
from fastapi import FastAPI, HTTPException
from .database import init_db, get_db_session, CallLog
from .cache import init_cache, query_cache, cache
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_cache()
    yield

app = FastAPI(lifespan=lifespan)

COST_PER_INPUT_TOKEN  = 0.00000025
COST_PER_OUTPUT_TOKEN = 0.00000125

@app.post("/generate", response_model=Response)
async def generate_response(request: Request):

    cache_result, latency_ms = await query_cache(request.prompt)
    
    if cache_result:
        return Response(
            response=cache_result.payload.response,
            model=request.model,
            input_tokens=0,
            output_tokens=0,
            latency_ms=round(latency_ms, 2),
            cost_usd=0
        )

    api_key = settings.anthropic_api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key not configured")

    start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": request.model, 
                "max_tokens": request.max_tokens,
                "messages": [{
                    "role": "user", 
                    "content": request.prompt
                    }]
            },
            timeout=30.0)

    data = res.json()
    latency_ms = (time.perf_counter() - start) * 1000
    text = data["content"][0]["text"]

    input_tokens = data["usage"]["input_tokens"]
    output_tokens = data["usage"]["output_tokens"]

    cost_usd = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)

    await cache(request.prompt, text)

    session = get_db_session()

     
    log = CallLog(
        prompt=request.prompt,
        model=request.model,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd
    )
    await session.add(log)
    await session.commit()

    return Response(response=text, model=request.model, latency_ms=round(latency_ms, 2), input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost_usd)

        

