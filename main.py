import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import webhook, trades, stats, settings, mode, signals, account, ws
from config import settings as app_settings
from services.signal_processor import SignalProcessor
from services.order_monitor import OrderMonitor
from database.db import engine, Base
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI(title="Crypto Algo Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Setup database (since we don't have active migrations runner here, let's create tables)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start the signal processor background task
    processor = SignalProcessor()
    asyncio.create_task(processor.start())

    # Start the order monitor background task
    monitor = OrderMonitor()
    asyncio.create_task(monitor.start())

    # Start the WS redis listener
    asyncio.create_task(ws.manager.listen_to_redis())

app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
app.include_router(trades.router, prefix="/trades", tags=["trades"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])
app.include_router(settings.router, prefix="/settings", tags=["settings"])
app.include_router(mode.router, prefix="/mode", tags=["mode"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(account.router, prefix="/account", tags=["account"])
app.include_router(ws.router, tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "Crypto Algo Bot API is running", "mode": app_settings.MODE}
