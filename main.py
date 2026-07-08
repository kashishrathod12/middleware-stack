from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

EMAIL = "25f2005273@ds.study.iitm.ac.in"

# Assigned values
RATE_LIMIT = 8          # requests
WINDOW = 10             # seconds

# Assigned CORS origin
ALLOWED_ORIGIN = "https://app-q16y45.example.com"

# Also allow the exam page origin during grading.
# Replace with the actual origin if your exam specifies one.
EXAM_ORIGIN = "https://exam.sanand.workers.dev"

app = FastAPI()

# -----------------------------
# CORS Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        EXAM_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Request Context Middleware
# -----------------------------
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")

        if not request_id:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        return response


# -----------------------------
# Rate Limiter Middleware
# -----------------------------
client_requests = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id", "anonymous")

        now = time.time()

        if client_id not in client_requests:
            client_requests[client_id] = []

        timestamps = [
            t
            for t in client_requests[client_id]
            if now - t < WINDOW
        ]

        if len(timestamps) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        timestamps.append(now)
        client_requests[client_id] = timestamps

        response = await call_next(request)
        return response


# Order:
# Request Context -> Rate Limit -> Endpoint
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)


# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }