import time
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import Request, Response, ProviderStats, StatsResponse
from fastapi import FastAPI, HTTPException, Depends
from .database import init_db, get_db_session, CallLog
from .config import settings
from .providers import ClaudeProvider, OpenAIProvider, ProviderRouter, TokenBucket
from .semantic_cache import semantic_cache
from .logger import setup_logging, logger
from sqlalchemy import func, select
import uuid
from structlog.contextvars import bind_contextvars, clear_contextvars

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("startup", message="LLM Gateway starting up")
    await init_db()
    await semantic_cache.init_cache()
    yield
    logger.info("shutdown", message="LLM Gateway shutting down")
    await semantic_cache.close()

app = FastAPI(lifespan=lifespan)

COST_PER_INPUT_TOKEN  = 0.00000025
COST_PER_OUTPUT_TOKEN = 0.00000125

provider_router = ProviderRouter([
    OpenAIProvider(),
    ClaudeProvider(),  
], rate_limits={
        "claude": TokenBucket(rate=1.0, capacity=5),
        "openai": TokenBucket(rate=1.0, capacity=5),
})

@app.middleware("http")
async def bind_request_id(request: Request, call_next):
    clear_contextvars()
    request_id = str(uuid.uuid4())[:8]
    bind_contextvars(request_id=request_id)
    logger.info("request_started", method=request.method, path=request.url.path)
    response = await call_next(request)
    logger.info("request_finished", status_code=response.status_code)
    return response

@app.post("/generate", response_model=Response)
async def generate_response(
    request: Request, 
    session: AsyncSession = Depends(get_db_session)
    ):

    logger.info("request_received", prompt_length=len(request.prompt), max_tokens=request.max_tokens)

    start = time.perf_counter()

    cached = await semantic_cache.get(request.prompt)

    cache_latency_ms = (time.perf_counter() - start) * 1000
    
    if cached:
        logger.info("cache_hit", prompt_length=len(request.prompt), latency_ms=round(cache_latency_ms * 1000, 2))
        return Response(
            response=cached,
            model="cached",
            input_tokens=0,
            output_tokens=0,
            latency_ms=round(cache_latency_ms, 2),
            cost_usd=0
        )
    
    logger.info("cache_miss", prompt_length=len(request.prompt))

    start = time.perf_counter()

    try:
        result = await provider_router.generate(
            prompt=request.prompt, 
            model=request.model, 
            max_tokens=request.max_tokens
            )

    except RuntimeError as e:
        logger.error("provider_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
    latency_ms = (time.perf_counter() - start) * 1000
    text = result.text

    input_tokens = result.input_tokens
    output_tokens = result.output_tokens 

    cost_usd = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)

    logger.info(
        "request_completed",
        model=result.model,
        latency_ms=round(latency_ms, 2),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        cache_hit=False
    )

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

        
@app.get("/stats", response_model=StatsResponse)
async def get_stats(session: AsyncSession = Depends(get_db_session)):

    overall = await session.execute(
        select(
            func.count(CallLog.id),
            func.avg(CallLog.latency_ms),
            func.sum(CallLog.cost_usd)
        )
    )

    total_calls, avg_latency, total_cost = overall.one()

    by_model_rows = await session.execute(
            select(
                CallLog.model,
                func.count(CallLog.id),
                func.avg(CallLog.latency_ms),
                func.sum(CallLog.cost_usd),
                func.avg(CallLog.input_tokens),
                func.avg(CallLog.output_tokens)
            ).group_by(CallLog.model)
        )

    by_model = {}
    for row in by_model_rows:
        by_model[row[0]] = ProviderStats(
            calls=row[1],
            avg_latency_ms=row[2],
            avg_cost_usd=row[3],
            avg_input_tokens=row[4],
            avg_output_tokens=row[5]    
        )

    cached_calls = by_model.pop("cached", None)
    cache_hits = cached_calls.calls if cached_calls else 0
    cache_hit_rate = round(cache_hits / total_calls, 4) if cache_hits else 0.0

    return StatsResponse(
        total_calls=total_calls,
        cache_hit_rate=cache_hit_rate,
        avg_latency_ms=avg_latency,
        total_cost_usd=total_cost,
        by_model=by_model
    )

        