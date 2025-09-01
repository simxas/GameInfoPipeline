import time
from fastapi import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import APIRouter

# --- Metric definitions ---
REQUESTS_TOTAL = Counter(
    'fastapi_requests_total',
    'Total number of HTTP requests.',
    ['method', 'endpoint']
)

REQUESTS_LATENCY = Histogram(
    'fastapi_http_request_duration_seconds',
    'HTTP request latency.',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

MODEL_INFERENCE_LATENCY = Histogram(
    'model_inference_duration_seconds',
    'Latency of AI model inference'
)

ERRORS_TOTAL = Counter(
    'fastapi_http_requests_failed_total',
    'Total number of HTTP requests that failed.',
    ['method', 'endpoint']
)

# --- Middleware ---
async def track_metrics(request: Request, call_next):
    method = request.method
    endpoint = request.url.path

    try:
        start_time = time.time()
        response = await call_next(request)
        latency = time.time() - start_time
        REQUESTS_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
    except Exception as e:
        ERRORS_TOTAL.labels(method=method, endpoint=endpoint).inc()
        raise e from None
    finally:
        REQUESTS_TOTAL.labels(method=method, endpoint=endpoint).inc()
    
    return response

# --- METRICS ENDPOINT ROUTER ---

# Use APIRouter to group the /metrics endpoint
metrics_router = APIRouter()

@metrics_router.get('/metrics')
async def metrics():
    return Response(content=generate_latest(), media_type='text/plain')