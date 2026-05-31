import os
import time
import httpx
from .schemas import Request, Response
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

async def connect_db():
    engine = await create_engine("postgresql+psycopg2://postgres:models_db@db:8080/DB")
    conn = engine.connect()
    print(conn)
    
    

@app.post("/generate", response_model=Response)
async def generate_response(request: Request):
    connect_db()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API Key not configured")

    start = time.perf_counter()

    with httpx.AsyncClient() as client:
        res = await client.post()

        if res.status != 200:
            raise HTTPException(status_code=res.status_code, detail=res.text)
        
    
    latency_ms = (time.perf_counter() - start ) * 1000

    return Response(response=res.data, model=request.model, latency_ms=latency_ms)
