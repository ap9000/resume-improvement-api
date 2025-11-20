This document serves as the Technical Design Specification (TDS) for the HireNewTalent Resume Engine. It is written for a Senior Software Engineer to implement immediately.Technical Specification: HNT Resume Engine (v1.0)MetadataDetailsStatusAPPROVEDOwnerEngineering LeadHostingRailway (PaaS)Core StackPython 3.11+, FastAPI, Redis (ARQ), Supabase, Gemini 1.5 FlashPrimary GoalHigh-fidelity resume parsing & rewriting at <$0.01 marginal cost per unit.1. Executive SummaryWe are building a dedicated microservice to decouple resume processing from the main hirenewtalent.ai monolith. This service will ingest raw user resumes (PDF/DOCX), extract structured data using OCR/LLMs, intelligently rewrite content for impact using Gemini 1.5 Flash, and re-render the result into a high-quality Microsoft Word (.docx) template using DocxTpl.Key Engineering ConstraintsAsynchronous by Design: Parsing/Generation takes 15-45s. API must be non-blocking.Strict Typing: All LLM outputs must adhere to rigid Pydantic schemas to prevent template breakage.Stateless Compute: The Railway services must be stateless; all artifacts persist in Supabase Storage.Cost Optimization: Use Gemini 1.5 Flash (tier 1 pricing) and minimal container resources.2. System ArchitectureThe system follows a Producer-Consumer pattern using a Redis-backed job queue.Code snippetsequenceDiagram
    participant Client as Frontend (React)
    participant API as FastAPI Gateway
    participant Redis as Redis Queue (ARQ)
    participant Worker as Python Worker
    participant Supabase as Supabase Storage
    participant LLM as Gemini 1.5 Flash

    Client->>API: POST /upload (File + TemplateID)
    API->>Supabase: Stream Upload (Raw Resume)
    API->>Redis: Enqueue Job {job_id, file_path, template_id}
    API->>Client: 202 Accepted {job_id}
    
    loop Poll Status
        Client->>API: GET /status/{job_id}
        API-->>Client: {status: "processing"}
    end

    Redis->>Worker: Pop Job
    Worker->>Supabase: Download Raw Resume
    Worker->>Worker: Parse Text (PyMuPDF)
    Worker->>LLM: Analyze & Rewrite (Structured JSON)
    LLM-->>Worker: JSON Data (Strict Schema)
    Worker->>Supabase: Download .docx Template
    Worker->>Worker: Render Template (Jinja2/DocxTpl)
    Worker->>Supabase: Upload Generated .docx
    Worker->>Redis: Update Job Status -> "completed"

    Client->>API: GET /status/{job_id}
    API-->>Client: {status: "completed", download_url: "..."}
3. Data & Storage Schema3.1 Supabase Storage StrategyWe will use Supabase Storage (S3-compatible) with three distinct folders/buckets to segregate data lifecycle.Bucket: resume-engine (Private, authenticated access only)/raw/{job_id}/{filename}: Original user uploads. Retention: 30 days./generated/{job_id}/{filename}: Final AI-written resumes. Retention: 30 days.Bucket: templates (Public Read)/{template_id}.docx: The master logic file with Jinja2 tags./{template_id}.png: Thumbnail for frontend UI.3.2 Data Contracts (Pydantic)This schema is the single source of truth. The LLM is forced to output this structure, and the Docx Template expects these exact variable names.Pythonfrom pydantic import BaseModel, Field
from typing import List, Optional

class WorkExperience(BaseModel):
    title: str = Field(..., description="Standardized job title")
    company: str = Field(..., description="Company name")
    date_range: str = Field(..., description="e.g., 'Jan 2020 - Present'")
    location: str = Field(..., description="City, State or Remote")
    bullets: List[str] = Field(..., description="3-5 action-oriented, impact-driven bullet points")

class Education(BaseModel):
    institution: str
    degree: str
    year: str

class ResumeSchema(BaseModel):
    full_name: str
    contact_email: str
    contact_phone: str
    linkedin_url: Optional[str] = None
    professional_summary: str = Field(..., description="A 3-sentence compelling bio")
    skills_technical: List[str] = Field(..., description="Hard skills (Python, SQL)")
    skills_soft: List[str] = Field(..., description="Soft skills (Leadership, Agile)")
    experience: List[WorkExperience]
    education: List[Education]
4. API Specification (FastAPI)Base URL: https://api.hirenewtalent.ai (or Railway provided URL)4.1 POST /api/v1/resumes/processIngests a file and queues the job.Multipart Form Data:file: Binary (PDF/DOCX)template_id: String (e.g., "modern_v1")Response (202 Accepted):JSON{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "eta_seconds": 30
}
4.2 GET /api/v1/resumes/status/{job_id}Checks job status.Response (Processing): {"status": "processing", "step": "analyzing_content"}Response (Success):JSON{
  "status": "completed",
  "download_url": "https://[supabase-project].supabase.co/storage/v1/object/sign/...",
  "expires_at": "2025-11-19T12:00:00Z"
}
Response (Error): {"status": "failed", "error": "Unable to extract text from corrupted PDF"}4.3 GET /api/v1/templatesReturns available templates for the frontend selector.Response:JSON[
  {
    "id": "modern_tech",
    "name": "Modern Tech",
    "thumbnail_url": "https://.../templates/modern_tech.png"
  }
]
5. Core Service Implementation Details5.1 The "Brain": Gemini 1.5 Flash IntegrationWe utilize Gemini's Controlled Generation (JSON Mode) to ensure the output matches our ResumeSchema strictly.Model: gemini-1.5-flashTemperature: 0.3 (Low creativity, high adherence to facts)System Prompt:"You are an expert Resume Editor. Your goal is to rewrite the user's experience to be results-oriented. Use active verbs. Do not hallucinate jobs. Output strict JSON."5.2 The "Builder": DocxTplTemplate Strategy: We do not generate XML from scratch. We use "Twin Files".Engine: docxtpl (Python).Logic:Download template_id.docx from Supabase to /tmp.Load into DocxTemplate.Inject ResumeSchema dictionary.Render and save to /tmp/{job_id}_out.docx.Upload to Supabase generated/.5.3 The "Engine": Redis & ARQWhy ARQ? It is built on asyncio, allowing the worker to handle concurrent network requests (uploading/downloading/calling LLM) much more efficiently than Celery's synchronous workers.Concurrency: Set max_jobs=10 per container to balance memory usage with throughput.6. Infrastructure & Deployment (Railway)6.1 railway.tomlWe will deploy a single Monorepo that spawns two services defined in the TOML.Ini, TOML[build]
builder = "docker"

# Service 1: The HTTP API
[[services]]
name = "api-gateway"
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
env = { WORKER_MODE = "false" }

# Service 2: The Background Worker
[[services]]
name = "job-worker"
startCommand = "arq app.worker.WorkerSettings"
env = { WORKER_MODE = "true" }
6.2 Environment VariablesRequired secrets in Railway Dashboard:VariableDescriptionGEMINI_API_KEYGoogle AI Studio KeySUPABASE_URLYour Project URLSUPABASE_SERVICE_KEYService Role Key (Bypasses RLS)REDIS_URLRailway Redis Connection String7. Implementation Plan (Step-by-Step)Phase 1: Foundation (Days 1-2)Repo Setup: Initialize Python FastAPI project with poetry or pip.Supabase: Create resume-engine (Private) and templates (Public) buckets.Redis: Spin up a Redis instance on Railway.Template: Create standard.docx with {{ full_name }} tags and upload to Supabase.Phase 2: The Worker (Days 3-4)Implement app/services/parser.py (PyMuPDF).Implement app/services/llm.py (Gemini + Pydantic).Implement app/services/generator.py (DocxTpl).Wire them together in an arq job function.Phase 3: The API & Frontend Hookup (Day 5)Build FastAPI endpoints.Implement "Signed URL" generation for downloads.Create the React "Template Selector" component.Phase 4: Hardening (Day 6)Add logging (Structlog).Add retry logic for LLM timeouts (Tenacity).Add error handling for "Unparseable PDF".8. Cost Projections (Bootstrapped Scale)Assuming 5,000 resumes / month:Railway (Compute): $5.00 (Shared Hobby tier is sufficient for V1).Redis: $5.00 (Railway Redis).Supabase: $0.00 (Free tier includes 500MB, we rotate files every 30 days).Gemini 1.5 Flash:Input: 5k resumes * 2k tokens * $0.075/1M = $0.75Output: 5k resumes * 1k tokens * $0.30/1M = $1.50Total AI Cost: ~$2.25 / month.Grand Total: ~$12.25 / month to process 5,000 resumes.9. Getting Started - Engineer's Checklist[ ] Git Clone the repo.[ ] Env File: Copy .env.example to .env and fill in Supabase/Gemini keys.[ ] Docker: Run docker-compose up to test Redis+API+Worker locally.[ ] Templates: Ensure at least one Valid Template is in your Supabase templates bucket.[ ] Test: Use Postman to hit POST /process with a sample PDF.