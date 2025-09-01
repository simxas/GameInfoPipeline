from fastapi import FastAPI
from llama_cpp import Llama
import os
from pydantic import BaseModel, Field
import time

# Import the specific metrics, middleware, and router
from monitoring.metrics import (
    MODEL_INFERENCE_LATENCY,
    track_metrics,
    metrics_router
)

app = FastAPI()

# Register metrics middleware
app.middleware('http')(track_metrics)

# Include the metrics router
app.include_router(metrics_router)

model_path = os.getenv('MODEL_PATH')

if not model_path:
    raise ValueError('MODEL_PATH environment variable not set.')

# Load the model
# n_ctx: The maximum number of tokens the model can handle in a single prompt/conversation.
# n_gpu_layers: Offloads all possible layers to the GPU.
llm = Llama(
    model_path=model_path,
    n_ctx=2048, # A common context size
    n_gpu_layers=100,
    verbose=True
)

# --- Pydantic model for request body ---
class PredictionRequest(BaseModel):
    prompt: str
    temperature: float = Field(0.7, gt=0, le=2.0)
    max_tokens: int = Field(512, gt=0)

# --- API Endpoints ---
@app.get('/')
def read_root():
    return {'message': 'API is running. Use the /predict endpoint to get model predictions'}

@app.post('/predict')
def predict(request: PredictionRequest):
    # Get the prompt and parameters from the request
    prompt = request.prompt
    temp = request.temperature
    max_tokens = request.max_tokens

    # start timer for model inference
    inference_start_time = time.time()

    # Reset the model's state before each new prediction
    llm.reset()
    # Generate a response from the model
    output = llm(
        prompt, 
        max_tokens=max_tokens,
        temperature=temp,
        stop=['\nHuman:', '\nQ:'] # Example stop sequences
    )

    # Extract the generated text
    response_text = output['choices'][0]['text']

    inference_latency = time.time() - inference_start_time
    MODEL_INFERENCE_LATENCY.observe(inference_latency)

    return {
        'response': response_text,
        'parameters': {
            'temperature': temp,
            'max_tokens': max_tokens
        }
    }

@app.post('/predict-test')
def predict(request: PredictionRequest):
    print(request)
    return {
        'response': 'TEST response!!!!!!'
    }
