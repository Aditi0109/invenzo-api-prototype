# 🚀 Dual-Core RAG Knowledge Engine & API Gateway

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

# Local Development Setup - Prerequisites:

Docker Desktop installed and running

Node.js (to run the data pusher script)

#Activate your local runtime configuration
.venv\Scripts\activate

#Install the application layer requirement matrices-
pip install -r requirements.txt
