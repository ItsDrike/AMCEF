import logging

from fastapi import FastAPI

from src.utils.log import setup_logging

log = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    """Perform initial setup."""
    setup_logging()
    log.info("API Server starting...")


@app.on_event("shutdown")
async def shutdown() -> None:
    """Perform cleanup."""
    log.info("API Server stopping...")
