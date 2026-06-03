from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from knowledge.dependencies import get_transport
from knowledge.routers.explanations import router as explanations_router
from shared_lib.logger import get_logger

log = get_logger("knowledge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    transport = get_transport()
    transport.connect()
    log.info("Conectado a PostgreSQL")
    yield
    transport.disconnect()
    log.info("Desconectado de PostgreSQL")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Knowledge API",
        description="Query persisted explanations with RAG augmentation for the solar pipeline",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(explanations_router)
    return app
