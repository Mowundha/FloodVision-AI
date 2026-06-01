# backend/main.py
# Complete FastAPI app with security, rate limiting, and all routers

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.routers import predict, streets, reports
from backend.utils.security import limiter, get_security_headers

# ── Create app ────────────────────────────────────────────────
app = FastAPI(
    title       = "FloodVision AI",
    description = "Street-level flood prediction for Tamil Nadu and Coastal India",
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc"
)

# ── Attach rate limiter to app ────────────────────────────────
# This makes the limiter work across all endpoints
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS middleware ───────────────────────────────────────────
# Allows Flutter app to call this API from any device
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"]
)

# ── Security headers middleware ───────────────────────────────
# Adds security headers to EVERY response automatically
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    This runs on every single request.
    After your endpoint returns a response,
    this adds security headers to it.
    """
    response = await call_next(request)
    headers  = get_security_headers()
    for key, value in headers.items():
        response.headers[key] = value
    return response

# ── Global error handler ──────────────────────────────────────
# If anything crashes, return clean JSON (not HTML error page)
# Flutter can always parse this
@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    print(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error":   "Internal server error",
            "detail":  str(exc)
        }
    )

# ── Register routers ──────────────────────────────────────────
app.include_router(predict.router, prefix="/api")
app.include_router(streets.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# ── Health check ──────────────────────────────────────────────
@app.get("/")
def health():
    return {
        "app":      "FloodVision AI",
        "status":   "running",
        "version":  "1.0.0",
        "coverage": "Tamil Nadu + all Indian coastal areas",
        "security": "rate-limiting + token verification + input sanitization",
        "endpoints": {
            "predict":        "POST /api/predict",
            "streets":        "GET  /api/streets",
            "notify_one":     "POST /api/notify/one",
            "notify_bulk":    "POST /api/notify/bulk",
            "submit_report":  "POST /api/reports/submit",
            "nearby_reports": "GET  /api/reports/nearby",
            "recent_reports": "GET  /api/reports/recent",
            "upvote_report":  "POST /api/reports/upvote",
            "get_report":     "GET  /api/reports/{id}",
            "docs":           "GET  /docs"
        }
    }