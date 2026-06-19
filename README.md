# Multi-Service E-Commerce AI Ecosystem & API Gateway

An enterprise-grade application ecosystem that integrates intelligent customer interaction, automated catalog workflows, and generative AI features. The platform combines:

- A context-isolated Retrieval-Augmented Generation (RAG) knowledge engine powered by Google Cloud's `Gemini 2.5 Flash` model and `FAISS` vector indexes
- A high-throughput automated bulk data processing subsystem
- A machine learning visualization layer

By unifying specialized microservices under a centralized application gateway, the architecture handles complex, data-heavy e-commerce workloads alongside real-time multimodal image synthesis.

---

## System Architecture Modules

### Dual-Core RAG Knowledge Engine

Maps technical microservice API routes side-by-side with general product help center documentation. Built with a Python Flask application layer, it separates unstructured help data from technical schema architectures into isolated vector indices (`faiss_api_index` vs `faiss_guides_index`) to eliminate data pollution, maintaining context integrity using automated session-RAM memory loops.

### Asynchronous Bulk Product Ingestion Engine - `Products_API`

A high-throughput FastAPI service capable of parsing large-scale catalog sheets (10,000+ rows) without blocking main application event loops. It implements multi-threaded background chunking, deterministic NLP text cleansing (NLTK tokenization and lemmatization), row-level data type normalization, and atomic MongoDB upserts, concluding with decoupled SMTP confirmation alerts upon batch completion.

### AI-Powered Virtual Try-On Pipeline - `vton_api`

A photorealistic apparel visualization service wrapping a 972M-parameter Multimodal Diffusion Transformer (MMDiT) model. The backend uses lifecycle memory pinning to bind model weights directly to GPU VRAM, and leverages an independent OpenCV HOG feature-descriptor filter to evaluate uploads upstream — preventing expensive graphics hardware calculation cycles from running on corrupted or non-human inputs.

---

## Features

| Feature | Description |
|---|---|
| **Context Isolation (Dual-Core Vector Space)** | Separates unstructured user help data from technical schema architectures into unique indices (`faiss_api_index` vs `faiss_guides_index`) to prevent data pollution and hallucinations. |
| **Dynamic Ingestion** | Pulls directly from the live OpenAPI configuration schema and programmatically parses live platform index layouts using regular-expression URL extractors. |
| **Dual Implementation** | Includes both the original Node.js/Express prototype and the migrated Python Flask production-ready codebase. |
| **Database Integration** | Local MongoDB persistence handling data streams seamlessly. |
| **Advanced Querying** | GET endpoints with case-insensitive substring searching and offset-based pagination (`page`, `limit`). |
| **Automation** | An automated JavaScript pusher script (`pusher.js`) to seed bulk dummy data via REST hooks. |
| **Orchestration** | Multi-container Docker Compose setup for instant deployment with isolated application and database layers. |
| **Asynchronous Bulk Product Ingestion** | A high-throughput FastAPI service (`Products_API`) processing large-scale (10,000+ rows) Excel sheets, with multi-threaded background chunking, row-level validation, NLP text cleansing, atomic MongoDB upserts, and decoupled SMTP completion emails. |
| **AI-Powered Virtual Try-On Engine** | A high-fidelity apparel visualization backend using a 972M-parameter MMDiT model to composite flat-lay garments onto user photos in pixel space. |

---

## Project Structure

```text
├── Day1_API/                   # Original Node.js / Express / Mongoose API
│   ├── models/                 # Mongoose schemas
│   ├── server.js               # Node application entry point
│   └── package.json
├── flask_api/                  # Migrated Python Flask / MongoEngine API
│   ├── models.py               # MongoEngine documents
│   ├── app.py                  # Flask routing & pagination engine
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Container recipe for Python service
├── Products_API/               # High-performance asynchronous bulk data pipeline
│   ├── .env                    # Scope-isolated connection and SMTP configuration secrets
│   ├── .env.example            # Version-controlled configuration schema template
│   ├── main.py                 # FastAPI application gateway & background task scheduler
│   ├── config.py               # Pydantic-Settings environment validation engine
│   ├── database.py             # Native PyMongo initialization & unique index maintenance
│   ├── nlp_utils.py            # Text normalization engine (NLTK tokenization & lemmatization)
│   └── requirements.txt        # Isolated dependency list for the bulk processing system
├── vton_api/                   # AI Virtual Try-On service (FASHN VTON 1.5 module)
│   ├── weights/                # Local directory containing network checkpoint assets (.gitignore isolated)
│   │   ├── model.safetensors   # 1.94 GB main MMDiT model checkpoint
│   │   └── dwpose/             # Auxiliary human pose-tracking layout structures
│   │       ├── yolox_l.onnx
│   │       └── dw-ll_ucoco_384.onnx
│   ├── scripts/
│   │   └── download_weights.py # Automated runtime weights downloader and network tool
│   ├── index.html              # Custom interactive web UI (vanilla JS, Fetch API, Base64 decoder)
│   ├── main.py                 # FastAPI gateway (lifecycle memory pinning & OpenCV guardrail filter)
│   ├── Dockerfile              # Multi-stage CUDA-backed runtime deployment blueprint
│   └── requirements.txt        # Isolated framework dependencies for the VTON subsystem
├── templates/
│   └── index.html              # Multi-tab asynchronous web UI for chatbot core
├── faiss_api_index/            # Vector compilation folder: grounded OpenAPI endpoint structural tokens
├── faiss_guides_index/         # Vector compilation folder: grounded help guide prose tokens
├── .env                        # Local environment variables and target AI access tokens
├── pusher.js                   # Axios-based automated data simulation script
├── docker-compose.yml          # Multi-container orchestration layer
├── app_web_chatbot.py          # Main web application gateway (orchestrates RAG routes, RAM state loops)
├── kajabi_chatbot.py           # Standalone CLI testing evaluation utility
├── kajabi_vector_pipeline.py   # RAG data ingestion pipeline (extracts docs, chunks text, generates FAISS embeddings)
└── requirements.txt            # Unified dependency configuration manifest for the target workspace root
```

---

## Module Deep Dive: Products Bulk Upload API

The `Products_API` submodule provides a structured, fail-safe architecture to process transactional catalog files cleanly without blocking main event loops.

**Technical architecture**

- **Non-blocking background workers** — Files are validated and acknowledged instantly with an HTTP 202 Accepted status. Long-running parsing jobs are offloaded natively using FastAPI `BackgroundTasks`.
- **Atomic MongoDB upserts** — Uses PyMongo's unordered `bulk_write` coupled with `UpdateOne(..., upsert=True)` operators. Timestamps are synced dynamically using `$setOnInsert` for `created_at` records and `$set` for `updated_at` modifications.
- **Deterministic NLP processing** — Title fields are tokenized, stripped of alphanumeric noise, filtered using English NLTK stopwords, and contextualized using the `WordNetLemmatizer` model into a clean `formatted_title` indexing string.
- **Robust error management** — Structural header checks validate data consistency out-of-band. Faulty rows (e.g. missing fields or bad price datatypes) are isolated and skipped individually, preventing cascade failures across processing batches.

---

## Module Deep Dive: AI Virtual Try-On API

The `vton_api` service implements a robust, client-agnostic virtual try-on pipeline optimized to handle complex garments (upper, lower, full-body cuts) over e-commerce payloads.

**Technical architecture**

- **Single-inference pinning** — To prevent heavy cold-start performance degradation, the underlying ~2 GB `TryOnPipeline` is instantiated once during application startup and pinned inside dedicated GPU VRAM.
- **Asynchronous worker thread offloading** — Heavily blocking deep-learning diffusion matrix computations are offloaded to an asynchronous background worker pool via FastAPI's `run_in_threadpool`, keeping the ASGI application fully responsive to incoming requests.
- **Independent input edge guardrails** — To maximize hardware optimization, requests pass through two pre-processing validation checks before execution:
  - *Guardrail A (Blur Assessment)*: Computes focus using an OpenCV Laplacian operator variance filter, filtering out unreadable or corrupted files upstream.
  - *Guardrail B (Human Shape Verification)*: Runs a localized OpenCV HOG descriptor and SVM pedestrian model. If an invalid image (e.g. a pet or landscape) is detected, execution halts immediately, avoiding unnecessary GPU sampling cycles.
- **Pixel-space diffusion modeling** — Unlike typical autoencoder solutions that downscale patterns into a lossy latent array, the architecture computes generation steps over raw pixel channels natively at 20 optimized timesteps, ensuring fabric weaves, graphics, and apparel details remain sharp.

---

## Local Development Setup

**Prerequisites**

- Docker Desktop installed and running
- Node.js (to run the data pusher script)

**Activate your local runtime configuration**

```bash
.venv\Scripts\activate
```

**Install the application layer requirement matrices**

```bash
pip install -r requirements.txt
```

### Products API Submodule Setup

1. Navigate to the feature directory:
   ```bash
   cd Products_API
   ```
2. Initialize environment configurations:
   ```bash
   cp .env.example .env
   ```
3. Configure your `MONGODB_URI` and SMTP details inside the created `.env` file.
4. Set up the local NLP dictionary dependencies:
   ```bash
   python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab')"
   ```
5. Execute the FastAPI local engine application layer:
   ```bash
   python main.py
   ```
6. Open the interactive Swagger interface at: `http://127.0.0.1:8000/docs`

### Virtual Try-On API Submodule Setup

1. Navigate to the microservice module folder:
   ```bash
   cd vton_api
   ```
2. Install isolated package dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Fetch the machine learning checkpoint matrices:
   ```bash
   python scripts/download_weights.py
   ```
4. Initialize the web server application layer:
   ```bash
   python main.py
   ```
5. Access the custom frontend dashboard at `http://localhost:8000/`, or inspect endpoint definitions at `http://localhost:8000/docs`.

**Endpoint specification**

| Field | Value |
|---|---|
| Endpoint | `POST /api/v1/try-on` |
| Payload type | `multipart/form-data` |
| Parameters | `person_image` (File), `garment_image` (File), `garment_type` (`upper_body` \| `lower_body` \| `full_body`), `output_format` (`jpeg` \| `png`) |
| Response | JSON object containing `result_image_url` (an inline, downloadable Base64 data URI string) and `inference_time_ms` (processing metric) |