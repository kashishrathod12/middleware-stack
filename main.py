from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

EMAIL = "25f2005273@ds.study.iitm.ac.in"

# Assigned values
RATE_LIMIT = 8
WINDOW = 10  # seconds

# Assigned CORS origin
ALLOWED_ORIGIN = "https://app-q16y45.example.com"

# IITM TDS grader origin
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
# Rate limit storage
# -----------------------------
client_requests = {}

# -----------------------------
# Combined Middleware
# -----------------------------
@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    # Request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    # Rate limiting
    client_id = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    timestamps = client_requests.get(client_id, [])
    timestamps = [t for t in timestamps if now - t < WINDOW]

    if len(timestamps) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
    else:
        timestamps.append(now)
        client_requests[client_id] = timestamps
        response = await call_next(request)

    # ALWAYS send the request ID back
    response.headers["X-Request-ID"] = request_id

    return response

# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }