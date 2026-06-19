import time
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Request, Response
from fastapi import FastAPI, HTTPException, Depends
from .database import init_db, get_db_session, CallLog
from .config import settings
from .providers import ClaudeProvider
from .semantic_cache import semantic_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await semantic_cache.init_cache()
    yield

    await semantic_cache.close()

app = FastAPI(lifespan=lifespan)

COST_PER_INPUT_TOKEN  = 0.00000025
COST_PER_OUTPUT_TOKEN = 0.00000125

claude_provide = ClaudeProvider()

@app.post("/generate", response_model=Response)
async def generate_response(
    request: Request, 
    session: AsyncSession = Depends(get_db_session)
    ):

    start = time.perf_counter()

    cached = await semantic_cache.get(request.prompt)

    cache_latency_ms = time.perf_counter() - start
    
    if cached:
        return Response(
            response=cached,
            model=request.model,
            input_tokens=0,
            output_tokens=0,
            latency_ms=round(cache_latency_ms, 2),
            cost_usd=0
        )

    api_key = settings.anthropic_api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key not configured")

    start = time.perf_counter()

    try:
        res = await claude_provide.generate(
            prompt=request.prompt, 
            model=request.model, 
            max_tokens=request.max_tokens
            )

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    latency_ms = (time.perf_counter() - start) * 1000
    text = res.text

    input_tokens = res.input_tokens
    output_tokens = res.output_tokens 

    cost_usd = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)

    await semantic_cache.set(request.prompt, text)
     
    log = CallLog(
        prompt=request.prompt,
        model=request.model,
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd
    )
    session.add(log)
    await session.commit()

    return Response(
        response=text, 
        model=request.model, 
        latency_ms=round(latency_ms, 2), 
        input_tokens=input_tokens, 
        output_tokens=output_tokens, 
        cost_usd=cost_usd
        )

        

