# Architecture: Agentic OCR System

## Overview
A web-based application utilizing Local LLMs (Qwen 2.5 Vision) for Optical Character Recognition (OCR) and document extraction, featuring a Human-in-the-Loop verification workflow.

## Core Intended Goal
Automate the extraction, verification, and settlement of claim insurance documents with a focus on messy handwritten notes and strict compliance (PII masking).

## Core Components
1.  **Presentation Layer**:
    *   **Claim Ingestion UI**: Multi-format upload (PDF, JPG, PNG) with auto-tiling visualization.
    *   **HITL Dashboard**: Side-by-side comparison for low-confidence (<90%) field triage.
2.  **Application Logic Layer**:
    *   **Pre-processor & Tiling Engine**: Converts PDF/Images to 300DPI tiles; maintains PageID->TileID hierarchy.
    *   **Orchestrator**: Antigravity Workflow Engine managing the "Ingest -> Extract -> Audit -> Review -> Settle" pipeline.
    *   **Shadow Auditor**:
        *   **Math Guard**: Verifies line item sums match totals (±0.01 tolerance).
        *   **PII Guard**: Masks SSNs/IDs in logs via Regex/NLP rules.
3.  **AI/ML Service Layer**: Local VLM Service (Qwen 2.5) via `LLMProvider`.
    *   **Contextual Anchoring**: Dynamically biases prompts based on Tile Coordinates (e.g., "Footer" implies "Medical Remarks").
4.  **Data Layer**:
    *   **Claim Data & Document Store**: Secure File System (served via Authenticated API).
    *   **Audit & Log Store**: PostgreSQL Database with PII-masked logs.

## Internal Backend Structure
The Python backend is structured to mirror the Application Logic Layer:
- `app/processor`: Tiling, PDF-to-Image (300DPI), and Page Structure management.
- `app/orchestrator`: Workflow state machine and confidence routing.
- `app/auditor`: "Shadow Auditor" logic (Math validation, PII Stripping).
- `app/llm`: Interface to Local VLM with Contextual Prompting.

## Vision Extraction Agent Prompt Strategy
This prompt uses **Contextual Anchoring** to help the local Qwen model interpret messy handwriting.

**System Instruction**: You are a "Claims Forensic Data Extractor."
**Context Input**: [Tile Image] + [Tile Coordinates/Type] (e.g., "Footer/PhysicianNotes").
**Dynamic Biasing**: If Tile == "Footer", expect "Diagnosis Codes" and "Cursive Remarks".

**Output Schema**:
```json
{
  "fields": {
    "diagnosis_code": { "value": "I10", "confidence": 0.95 },
    "physician_notes": { "value": "Patient shows signs of...", "confidence": 0.45, "needs_review": true }
  },
  "metadata": {
    "math_check": "model_calculated_sum", 
    "pii_detected": false
  }
}
```

## HITL Dashboard UI Design
The Human-in-the-Loop dashboard is the "Safety Valve".
- **Trigger**: Any field with Confidence < 90% OR Shadow Auditor Flag (Math Mismatch).
- **UI Components**:
    - **Side-by-Side View**: Original Crop vs. Extracted Text.
    - **Amber Alert**: Visual highlighting for low confidence.
    - **One-Click Verify**: "Confirm" or "Edit & Approve".

## 🛠 Tech Stack
- **Engine:** Python 3.12+ (FastAPI).
- **OCR Logic:** Qwen 2.5 Vision (Local).
- **Frontend:** React + Vite (Tailwind CSS for "Premium" Aesthetic).
- **Security:** Python-Magic (MIME Validation), Strict CORS, Authenticated Static Serving.

## System Architecture Diagram (Mermaid)

```mermaid
graph TD
    subgraph Presentation_Layer [Presentation Layer]
        UploadUI[Upload & Tiling UI]
        ReviewUI[HITL Request Dashboard]
        style UploadUI fill:#2d3748,stroke:#4fd1c5,color:#fff
        style ReviewUI fill:#c05621,stroke:#fbd38d,color:#fff
    end

    subgraph Application_Logic_Layer [Application Logic Layer]
        API[API Gateway]
        Processor[Tiling Engine]
        Orchestrator[Workflow Orchestrator]
        Auditor[Shadow Auditor]
        
        style API fill:#2c5282,stroke:#63b3ed,color:#fff
        style Processor fill:#2c5282,stroke:#63b3ed,color:#fff
        style Orchestrator fill:#2c5282,stroke:#63b3ed,color:#fff
        style Auditor fill:#e53e3e,stroke:#feb2b2,color:#fff
    end

    subgraph AI_Service_Layer [AI/ML Service Layer]
        LLM_Provider[LLM Provider (Context Aware)]
        Qwen[Local Qwen 2.5 VL]
        
        style LLM_Provider fill:#744210,stroke:#f6e05e,color:#fff
        style Qwen fill:#744210,stroke:#f6e05e,color:#fff
    end

    subgraph Data_Layer
        RawStore[Raw Processing Store]
        Archive[Secure Archive (Settled)]
        DB[Audit DB (PII Masked)]
    end

    %% Flow
    UploadUI -->|PDF/Images| API
    API --> Orchestrator
    Orchestrator -->|1. Ingest| Processor
    Processor -->|Tiles + Coords| Orchestrator
    
    Orchestrator -->|2. Extract (w/ Context)| LLM_Provider
    LLM_Provider --> Qwen
    Qwen --> LLM_Provider
    
    Orchestrator -->|3. Validate| Auditor
    Auditor -->|Math/PII Check| Orchestrator
    
    Orchestrator -->|4. If Low Conf/Flag| ReviewUI
    ReviewUI -->|Manual Fix| Orchestrator
    
    Orchestrator -->|5. Settle| Archive
    Orchestrator -->|Log| DB
```