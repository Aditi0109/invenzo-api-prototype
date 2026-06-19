# Dual-Core RAG Knowledge Engine & API Gateway

An advanced, context-isolated Retrieval-Augmented Generation (RAG) platform built with a Python Flask backend application layer, standard vector indexing structures (`FAISS`), and Google Cloud's `Gemini 2.5 Flash` core foundational LLM model. 

This platform maps technical microservice API routes side-by-side with general product knowledge documentation, utilizing an automated state management loop for conversation session memory tracking.

## 🚀 Features
* **Context Isolation (Dual-Core Vector Space):** Separates unstructured user help data from technical schema architectures into unique indices (faiss_api_index vs faiss_guides_index) to completely prevent data pollution and hallucinations.
* **Dynamic Ingestion Ingestion:** Pulls directly from the live OpenAPI standard configuration schema and programmatically parses live platform index layouts utilizing regular expression URL extractors.

* **Dual Implementation:** Includes both the original Node.js/Express prototype and the migrated Python Flask production-ready codebase.
* **Database Integration:** Local MongoDB persistence handling data streams seamlessly.
* **Advanced Querying:** GET endpoints equipped with case-insensitive substring searching and offset-based pagination (`page`, `limit`).
* **Automation:** An automated JavaScript pusher script (`pusher.js`) to seed bulk dummy data via REST hooks.
* **Orchestration:** Multi-container Docker Compose setup for instant deployment with isolated application and database layers.
* **Asynchronous Bulk Product Ingestion:** A high-throughput FastAPI service (Products_API) capable of processing large-scale (10,000+ rows) Excel sheets. It handles multi-threaded background chunking, custom row-level validation, NLP text cleansing, atomic MongoDB upserts, and decoupled SMTP email completions.

---

## 📂 Project Structure
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
├── Products_API/               # High-Performance Asynchronous Bulk Data Pipeline
│   ├── .env                    # Scope-isolated connection and SMTP configuration secrets
│   ├── .env.example            # Version-controlled configuration schema template
│   ├── main.py                 # FastAPI application gateway & background task scheduler
│   ├── config.py               # Pydantic-Settings environment validation engine
│   ├── database.py             # Native PyMongo initialization & unique index maintenance
│   ├── nlp_utils.py            # Text normalization engine (NLTK Tokenization & Lemmatization)
│   └── requirements.txt        # Isolated dependency list for the bulk processing system
├── templates/                 
│   └── index.html              # Multi-tab asynchronous Web UI (Vanilla JS, Fetch API, CSS Engine)
├── faiss_api_index/            # Vector compilation folder: Grounded OpenAPI endpoint structural tokens
├── faiss_guides_index/         # Vector compilation folder: Grounded help guide prose tokens
├── .env                        # Local environment variables and target AI access tokens 
├── pusher.js                   # Axios-based automated data simulation script
├── docker-compose.yml          # Multi-container orchestration layer
├── app_web_chatbot.py          # Main Web Application Gateway (Orchestrates RAG routes, RAM state loops)
├── kajabi_chatbot.py           # Standalone Command-Line Interface (CLI) testing evaluation utility
├── kajabi_vector_pipeline.py   # RAG Data Ingestion pipeline (Extracts docs, chunks text, and generates FAISS embeddings)
└── requirements.txt            # Unified dependency configuration manifest for the target workspace root

```
## Module Deep Dive: Products Bulk Upload API
The Products_API submodule provides a structured, fail-safe architecture to process transactional catalogue files cleanly without blocking main event loops.

### Technical Architecture
* **Non-Blocking Background Workers:** Files are validated and acknowledged instantly with an HTTP 202 Accepted status. Long-running parsing jobs are offloaded natively using FastAPI BackgroundTasks.
* **Atomic MongoDB Upserts:** Uses PyMongo’s unordered bulk_write coupled with UpdateOne(..., upsert=True) operators. Timestamps are synced dynamically using $setOnInsert for created_at records and $set for updated_at modifications.
* **Deterministic NLP Processing:** Title fields are tokenized, stripped of alphanumeric noise, filtered using English NLTK stopwords, and contextualized using the WordNetLemmatizer model into a clean formatted_title indexing string.
* **Robust Error Management:** Structural header checks validate data consistency out-of-band. Faulty row rows (e.g., missing fields or bad price datatypes) are isolated and skipped individually, preventing cascade failures across processing batches.

## Local Development Setup - Prerequisites:

Docker Desktop installed and running

Node.js (to run the data pusher script)

#Activate your local runtime configuration

.venv\Scripts\activate

#Install the application layer requirement matrices

pip install -r requirements.txt

## Products API Submodule Setup

1.Navigate to the feature directory:

cd Products_API

2.Initialize environment configurations:

cp .env.example .env

3.Configure your MONGODB_URI and SMTP details inside the created .env file.

4.Set up the local NLP dictionary dependencies:

python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab')"

5.Execute the FastAPI local engine application layer:

python main.py

6.Open interactive interface swagger schemes at: http://127.0.0.1:8000/docs