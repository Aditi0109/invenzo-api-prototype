# Virtual Try-On API Backend Module (FASHN VTON 1.5)

This directory implements the core asynchronous web interface wrapping the Multimodal Diffusion Transformer try-on system.

## Local Configuration Flow

### 1. Build Isolated Runtime Environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Pre-fetch Pipeline Asset Arrays
```bash
python scripts/download_weights.py
```

