# Unified API Prototype (Node.js / Python Flask / MongoDB)

A containerized backend service built during my internship at Invenzo Labs. This repository contains the progression of an inventory/item management API, originally developed in Node.js/Express, translated into Python Flask using MongoEngine, enhanced with enterprise-level search/pagination parameters, and fully containerized using Docker.

## 🚀 Features
* **Dual Implementation:** Includes both the original Node.js/Express prototype and the migrated Python Flask production-ready codebase.
* **Database Integration:** Local MongoDB persistence handling data streams seamlessly.
* **Advanced Querying:** GET endpoints equipped with case-insensitive substring searching and offset-based pagination (`page`, `limit`).
* **Automation:** An automated JavaScript pusher script (`pusher.js`) to seed bulk dummy data via REST hooks.
* **Orchestration:** Multi-container Docker Compose setup for instant deployment with isolated application and database layers.

---

## 📂 Project Structure
```text
├── Day1_API/            # Original Node.js / Express / Mongoose API
│   ├── models/          # Mongoose schemas
│   ├── server.js        # Node application entry point
│   └── package.json     
├── flask_api/           # Migrated Python Flask / MongoEngine API
│   ├── models.py        # MongoEngine documents
│   ├── app.py           # Flask routing & pagination engine
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile       # Container recipe for Python service
├── pusher.js            # Axios-based automated data simulation script
└── docker-compose.yml   # Multi-container orchestration layer

```

Local Development Setup - Prerequisites:
Docker Desktop installed and running
Node.js (to run the data pusher script)
