"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    print("🚀 Starting Weekly AI Sigint...")
    await init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Weekly AI Sigint",
    description="AI/enterprise tech content aggregator and synthesizer",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint."""
    return """
    <html>
        <head>
            <title>Weekly AI Sigint</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                }
                h1 { color: #1a73e8; }
                .status { color: #0d652d; }
                a { color: #1a73e8; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Weekly AI Sigint</h1>
            <p class="status">✅ System online</p>
            <p>A locally-hosted app that fetches AI/enterprise tech content weekly, synthesizes briefings with Claude, and exports to Notion/Slack.</p>
            <h2>Quick Links</h2>
            <ul>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/health">Health Check</a></li>
            </ul>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "weekly-ai-sigint",
        "version": "1.0.0"
    }
