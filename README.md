# GameInfoPipeline

Hey there! Welcome to my project.

### A Quick Word on This Project

First off, this is a **learning project**. I built it to get hands-on experience with a bunch of different technologies and make them all work together. It's my personal sandbox for diving into microservices, containerization, and MLOps principles.

**My Approach to AI:** I want to be upfront about my use of AI. The code for the application logic and infrastructure is my own. I used AI as a powerful research tool—think of it as "Stack Overflow on steroids." It was great for getting quick examples of library usage or understanding concepts, but I never fed my own code to it and asked for solutions. The goal was to learn, not to have something built for me. (The only exception is the HTML/CSS for the two web pages, because life's too short to become a CSS guru overnight!)

---

## What is this thing?

The `GameInfoPipeline` is a simple web app with a powerful backend. You give it the name of a video game and its platform, and it gives you back:

*   Official game info like the release date and rating.
*   The game's cover art.
*   A unique, short review generated on the fly by a local AI model running on a dedicated backend service.

It's basically a fun way to combine external API data with local AI inference.

## How It Works (The Architecture)

The whole application runs as a set of containerized services that talk to each other over a private network, all managed by Docker Compose.

Here are the pieces:

1.  **The Frontend (`Flask` service):**
    *   This is the user-facing part of the app. It's a simple Flask application that serves the web pages.
    *   When you submit the form, this service calls two different APIs: the external RAWG API for game data and our own internal backend for the AI review.

2.  **The Backend (`FastAPI` service):**
    *   A dedicated, GPU-accelerated FastAPI service. Its only job is to host a local Large Language Model (LLM) using `Llama-cpp-python`.
    *   It exposes a single endpoint that the frontend calls to generate game reviews.

3.  **The Monitoring Stack (`Prometheus` & `Grafana`):**
    *   Both the frontend and backend applications are instrumented to expose performance metrics (like request latency and counts).
    *   Prometheus is configured to automatically discover and scrape these metrics from the services.
    *   Grafana is connected to Prometheus, giving you a place to build dashboards and visualize how the application is performing in real-time.

## Tech Stack

*   **Frontend:** Python, Flask, Requests
*   **Backend:** Python, FastAPI, Llama-cpp-python
*   **Infrastructure:** Docker, Docker Compose, NVIDIA CUDA
*   **Monitoring:** Prometheus, Grafana

---

## Getting Started

Ready to run it yourself? Here’s how.

### Prerequisites

*   **Docker and Docker Compose:** The core of the application's infrastructure.
*   **A GGUF-formatted language model:** You'll need to download a model to place in your `models` directory (e.g., from Hugging Face).
*   **GPU Acceleration Setup (for WSL2):** For the AI backend to work with your GPU inside a Docker container on WSL2, you need a specific setup:
    1.  **Host Machine (Windows):** Ensure you have the latest NVIDIA drivers installed (e.g., the Studio or Game Ready drivers).
    2.  **WSL2 Environment (Ubuntu):** You must install the **NVIDIA CUDA Toolkit for WSL**. This is the key component that allows Docker Desktop to access the GPU from within your Linux environment. The specific version I used can be found here: [CUDA Toolkit 12.6.3 for WSL-Ubuntu 2.0](https://developer.nvidia.com/cuda-12-6-3-download-archive?target_os=Linux&target_arch=x86_64&Distribution=WSL-Ubuntu&target_version=2.0&target_type=deb_local).

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/GameInfoPipeline.git
cd GameInfoPipeline
```

### 2. Set Up Your Environment Files

This project uses `.env` files to handle secrets and configuration. You'll need to create three of them.

*   **Frontend Configuration:**
    *   Copy the example file: `cp services/frontend/.env.example services/frontend/.env`
    *   Now, edit `services/frontend/.env` and paste in your personal API key from [rawg.io](https://rawg.io/apidocs).

*   **Backend Configuration:**
    *   The backend's `.env` file tells the application where to find the model *inside the container*. You just need to copy the example file for this to work:
    *   `cp services/backend/.env.example services/backend/.env`

*   **Docker Compose Configuration (IMPORTANT!):**
    *   Create one more `.env` file in the main project root: `touch .env`
    *   Open this new `.env` file and add the following line, replacing the path with the **absolute path** to the folder on your computer where you will store your AI models:
    ```
    MODEL_PATH=/home/your-user/path/to/your/models
    ```

### 3. Place Your AI Model

*   Take your `.gguf` model file and place it inside the folder you specified in the `MODEL_PATH` variable above. For example, if your `MODEL_PATH` is `/home/simon/AI/models`, place your model file in that directory.

### 4. Build and Run!

Now for the easy part. Just run one command from the root directory of the project:

```bash
docker compose up -d --build
```

This will build the Docker images for the frontend and backend, pull the images for Prometheus and Grafana, and start everything up in the correct order.

## How to Use the App

Once the containers are up and running, here’s where you can find everything:

*   **The Web App:** [http://localhost:5000](http://localhost:5000)
*   **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Prometheus UI:** [http://localhost:9090](http://localhost:9090)
*   **Grafana UI:** [http://localhost:3000](http://localhost:3000) (login with `admin` / `admin`)