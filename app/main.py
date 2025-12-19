"""
FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .api.routes import router
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Crawler Service...")
    settings = get_settings()
    print(f"📡 Base URL: {settings.base_url}")
    print(f"🗄️  Supabase: {settings.supabase_url}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Crawler Service...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="🕷️ Truyện Crawler Service",
        description="""
## Web Crawler API for truyenfull.vision

A robust, scalable web crawler service built with:
- **FastAPI** - Modern async API framework
- **Playwright** - Headless browser automation
- **Supabase** - PostgreSQL database
- **Celery + Redis** - Async task queue

### Features
- 🕸️ Stealth crawling with anti-detection
- 📚 Story and chapter extraction
- 🔄 Async job processing
- 📊 RESTful API with auto-docs
        """,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(router)
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
