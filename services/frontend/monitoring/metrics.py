import time
from flask import request, Response, g
from prometheus_client import Counter, Histogram, generate_latest

# --- Metric definitions ---
REQUESTS_TOTAL = Counter(
    'flask_requests_total',
    'Total number of HTTP requests.',
    ['method', 'endpoint']
)

REQUESTS_LATENCY = Histogram(
    'flask_http_request_duration_seconds',
    'HTTP request latency.',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ERRORS_TOTAL = Counter(
    'flask_http_requests_failed_total',
    'Total number of HTTP requests that failed.',
    ['method', 'endpoint']
)

EXTERNAL_API_LATENCY = Histogram(
    'ext_api_duration_seconds',
    'Latency of RAWG API calls made by Flask client app.',
    ['api_name'], # A label to distinguish between FastAPI and RAWG.io
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# --- FLASK REGISTRATION FUNCTION ---
# This is the core logic that hooks into Flask.
def register_metrics(app):
    """
    Registers Prometheus metrics tracking for the Flask app.
    This function sets up before_request and teardown_request handlers.
    """

    @app.before_request
    def start_timer():
        """
        Starts a timer at the beginning of each request.
        Uses Flask's 'g' object to store the start time.
        """
        g.start_time = time.time()
    
    @app.teardown_request
    def record_metrics(exception=None):
        """
        Records metrics at the end of each request.
        This function is guaranteed to run, even if an exception occurs.
        """
        # Ensure start_time was set
        if 'start_time' in g:
            # Calculate total request latency
            latency = time.time() - g.start_time

            endpoint = request.path
            method = request.method

            # Record the latency in our histogram
            REQUESTS_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

            # Increment the total requests counter
            REQUESTS_TOTAL.labels(method=method, endpoint=endpoint).inc()

            # If the request resulted in an exception, increment the error counter
            if exception:
                ERRORS_TOTAL.labels(method=method, endpoint=endpoint).inc()


# --- METRICS ENDPOINT (using a Flask Blueprint) ---
from flask import Blueprint

# Create a Blueprint, which is Flask's way of organizing a group of routes
metrics_blueprint = Blueprint('metrics', __name__)

@metrics_blueprint.route('/metrics')
def metrics():
    """
    The /metrics endpoint for Prometheus to scrape.
    """
    return Response(generate_latest(), mimetype='text/plain')