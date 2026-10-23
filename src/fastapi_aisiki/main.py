from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq import create_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi_aisiki.api.v1.router import api_router
from fastapi_aisiki.core.config import settings
from fastapi_aisiki.core.exceptions import register_exception_handlers
from fastapi_aisiki.core.logging import setup_logging
from fastapi_aisiki.core.queue import ArqTaskQueue, get_redis_settings
from fastapi_aisiki.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    redis_pool = await create_pool(get_redis_settings())
    app.state.queue = ArqTaskQueue(redis_pool)
    yield
    await redis_pool.aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
        openapi_url=None if settings.is_production else f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
    )

    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
