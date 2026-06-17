# Use a lightweight official PyTorch runtime containing preconfigured CUDA drivers
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /workspace

# Install system utilities required for OpenCV pixel array manipulations
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Cache dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bring codebase assets into scope
COPY . .

# Expose server listener port
EXPOSE 8000

# Fire up server runtime engine
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]