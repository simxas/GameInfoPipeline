FROM nvidia/cuda:12.6.3-cudnn-devel-ubuntu24.04

RUN apt-get update && \
    apt-get install -y git python3.12 python3.12-venv python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser

WORKDIR /home/appuser/app

RUN mkdir /models

RUN python3 -m venv /opt/venv
RUN chown -R appuser:appuser /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=appuser:appuser requirements.txt requirements.txt

ARG CMAKE_ARGS="-DGGML_CUDA=on" 
ENV FORCE_CMAKE=1

RUN pip install --no-cache-dir -r requirements.txt

ARG CMAKE_ARGS=""

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]