# Agentic OCR System (OCRAgent)

## Overview
A next-generation OCR application built with an "Agent-First" architecture, specifically designed for processing complex insurance claim documents. OCRAgent leverages Local LLMs (Qwen 2.5 Vision) to extract structured data from typed and handwritten text, featuring a robust "Shadow Auditor" for compliance and a side-by-side Human-in-the-Loop (HITL) verification dashboard.

## Architecture & Domains
The system is organized into four core functional domains:
1.  **Claim Ingestion & Pre-processing**: Handles multi-format uploads (PDF, JPG, PNG) and generates high-DPI tiles for granular analysis.
2.  **AI Extraction & Semantic Analysis**: Uses contextual anchoring to guide the VLM in extracting high-fidelity data with confidence scoring.
3.  **Quality Gate & Compliance**: The "Shadow Auditor" performs mathematical validation and global PII masking.
4.  **HITL & Finalization**: Provides a triage queue for low-confidence data and automates the settlement/archival process.

## Tech Stack
### Backend
- **Engine**: Python 3.12+ (FastAPI)
- **Database**: PostgreSQL (Docker) / SQLite (Fallback)
- **OCR/LLM**: Qwen 2.5 Vision (via `LLMProvider` interface)
- **Key Libraries**: `SQLAlchemy`, `pdf2image`, `Pillow`, `openai` (API wrapper)

### Frontend
- **Framework**: React + Vite
- **Styling**: Tailwind CSS / Lucide React
- **State/Routing**: React Router, Axios

## Status
- [x] **Initialization**: Project structure and agentic framework established.
- [x] **Domain 1**: Ingestion pipeline complete.
- [x] **Domain 2**: Context-aware AI extraction implemented.
- [x] **Domain 3**: Shadow Auditor & PII masking complete.
- [x] **Domain 4**: HITL Review & Settlement logic implemented.
- [x] **Verification**: End-to-end pipeline validated via automation.
- [x] **Frontend**: UI integrated with all backend services.
- [x] **Workflow**: 2-Stage Approval (Resolve -> Audited -> Completed) implemented.

## Environment Configuration

### Database Reset
To clear all data during development:
```bash
python backend/scripts/reset_db.py
```
*Note: This wipes all claims and extractions.*

### 1. Environment Variables (`.env`)
Create a `.env` file in the root directory with the following variables:
```env
# LLM Configuration (e.g., Ollama or LM Studio)
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5-vision

# Database Configuration
POSTGRES_USER=ocr_user
POSTGRES_PASSWORD=ocr_password
POSTGRES_DB=ocr_db

# Security & Paths
DATA_DIR=data
FRONTEND_URL=http://localhost:5173
```

### 2. Database (Docker)
The system uses PostgreSQL for persistence. Ensure Docker is installed and run:
```bash
docker-compose up -d
```
This starts the database on `localhost:5432`.

### 3. Local LLM Setup (Qwen 2.5)
The system requires a local vision-language model.
- **Option A: Ollama (Recommended)**
  1. Install [Ollama](https://ollama.com/).
  2. Pull the model: `ollama pull qwen2.5-vision`.
  3. Verify: `curl http://localhost:11434/v1/models`.
- **Option B: LM Studio**
  1. Load `Qwen 2.5 Vision` and start the Local Server on port 1234.
  2. Update `LLM_BASE_URL` in `.env` accordingly.

## Startup Guide

### Step 1: Start Infrastructure
```bash
docker-compose up -d  # Start Database
# Ensure Ollama/LM Studio is running
```

### Step 2: Backend Setup & Start
1. Navigate to `backend/`:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Step 3: Frontend Setup & Start
1. Navigate to `frontend/`:
   ```bash
   npm install
   ```
2. Start the Vite server:
   ```bash
   npm run dev
   ```

### Step 4: Environment Parameter Audit
Before proceeding to verification, ensure all parameters in your environment files are synchronized:

#### 1. Backend LLM Configuration (`.env`)
The backend needs to know where your local LLM is hosted:
- **Endpoint**: `LLM_BASE_URL` (Default: `http://localhost:11434/v1` for Ollama)
- **Model**: `LLM_MODEL=qwen2.5-vision` (Must match the model pulled in Step 3)
- **API Key**: `LLM_API_KEY=ollama` (Use `lm-studio` if using LM Studio)

#### 2. Frontend API Configuration (`frontend/.env`)
The frontend needs the backend's API endpoint. Create a `frontend/.env` file:
```env
VITE_API_URL=http://localhost:8000/api/v1/claims
```
> [!NOTE]
> If you haven't refactored the frontend to use `import.meta.env.VITE_API_URL`, the current hardcoded URL is located in `frontend/src/api/claims.ts`.

### Step 5: Verify Integration
Visit `http://localhost:5173`. Upload a sample claim (JPG/PNG) to test the `Ingest -> Extract` flow.



## Verification & Test Results
The system has been validated using an automated E2E pipeline:
- **Domain 1-4 Logic**: Verified via `pytest backend/tests/`.
- **CORS & Connectivity**: E2E tests confirmed frontend/backend communication (Note: Ensure origin matching in `app/main.py`).
- **OCR Accuracy**: Qwen 2.5 Vision successfully extracts both typed and handwritten fields with high confidence (>0.90 for clear text).

## Known Issues
- **Poppler Dependency**: PDF ingestion requires `poppler`.
  - **Mac**: `brew install poppler`
  - **Linux**: `sudo apt-get install poppler-utils`
  - **Windows**: Download binary and add to PATH.

