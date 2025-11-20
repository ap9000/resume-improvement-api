# Resume Engine v2.0 - Implementation Plan

## 🎯 Strategic Goals
- **Scalability:** Handle 10k+ resumes/month without breaking
- **User Experience:** Professional async job processing with status tracking
- **Cost Efficiency:** <$0.01/resume marginal cost (target: $0.0011/resume)

## 📊 Current State Assessment

### ✅ What's Working (Keep)
- FastAPI application with proper structure
- Resume analysis scoring system (5 categories, 100 points)
- Claude AI integration with retry logic
- PDF generation from HTML templates
- 4 professional resume templates
- Supabase storage with signed URLs
- API key authentication & rate limiting
- Health check endpoints

### ⚠️ What's Different from Spec
- **Architecture:** Synchronous endpoints vs async job queue
- **AI Provider:** Claude 3.5 Sonnet vs Gemini 1.5 Flash (47x more expensive!)
- **Output Format:** HTML→PDF vs DOCX templates
- **Parser:** External Railway API vs internal PyMuPDF

### ❌ What's Missing
- ARQ job queue + Redis
- Background worker container
- Persistent job status tracking
- Database tables/migrations
- Internal resume parser
- Several TODO implementations

---

## 💰 Cost Analysis & Recommendations

### Current vs Proposed Costs (per 1,000 resumes)

| Component | Current | Proposed | Savings |
|-----------|---------|----------|---------|
| AI (Claude vs Gemini) | $21.00 | $0.45 | $20.55 |
| Infrastructure | $10.00 | $15.00 | -$5.00 |
| **Total** | **$31.00** | **$15.45** | **$15.55** |

### At Scale (10,000 resumes/month)
- **Current:** $310/mo
- **Proposed:** $154.50/mo
- **Annual Savings:** $1,866

### Key Decision: Gemini 1.5 Flash + PDF
**Recommendation:** Migrate to Gemini but KEEP PDF output

**Rationale:**
1. 47x cost reduction ($21 → $0.45 per 1k resumes)
2. Gemini 1.5 Flash is excellent at structured tasks
3. PDF is more professional than DOCX for this use case
4. Don't rewrite working PDF generator
5. Can add DOCX as premium feature later if needed

**Action:** Test Gemini quality on 20-30 resumes before full migration

---

## 🏗️ Architecture Decision: Full Async

### Why Async Job Queue (ARQ + Redis)?

**UX Benefits:**
- No 30-45s hanging requests
- Professional polling experience
- Automatic retry on failures
- Progress tracking

**Technical Benefits:**
- Horizontal scaling (add workers)
- Job persistence
- Better error handling
- Production-grade pattern

**Cost:**
- +$5/mo for Redis
- ~3-5 days dev time
- **Worth it:** UX is king in 0-1, and resume processing IS inherently async

---

## 📋 Implementation Phases

### Phase 1: Core Migration (Days 1-3) ⚡ CRITICAL PATH

#### 1.1 Add ARQ + Redis Job Queue
**Files to create:**
- `app/worker.py` - ARQ worker with WorkerSettings
- `app/services/queue.py` - Job queue management utilities

**Files to modify:**
- `requirements.txt` - Add `arq==0.25.0`, `redis==5.0.1`
- `app/utils/config.py` - Add REDIS_URL, ARQ settings
- `app/routers/analyze.py` - Convert to job submission
- `app/routers/improve.py` - Convert to job submission
- `app/routers/generate.py` - Convert to job submission

**Tasks:**
- [ ] Install Redis on Railway
- [ ] Create worker.py with job functions
- [ ] Implement job enqueueing in queue.py
- [ ] Add job status tracking in Redis
- [ ] Update all endpoints to return job_id
- [ ] Test job flow end-to-end

**New Endpoint Pattern:**
```python
# Before (synchronous)
POST /api/v1/analyze → {scores, issues, suggestions} (30s wait)

# After (async)
POST /api/v1/analyze → {job_id, status: "queued"} (instant)
GET /api/v1/status/{job_id} → {status: "processing|completed|failed"}
GET /api/v1/result/{job_id} → {scores, issues, suggestions}
```

#### 1.2 Migrate to Gemini 1.5 Flash
**Files to create:**
- `app/services/gemini_improver.py` - New Gemini-based improver
- `scripts/test_gemini_quality.py` - Quality comparison script

**Files to modify:**
- `requirements.txt` - Add `google-generativeai==0.3.2`
- `app/utils/config.py` - Add GEMINI_API_KEY
- `app/routers/improve.py` - Swap to Gemini service (after testing)

**Tasks:**
- [ ] Add Gemini SDK to requirements
- [ ] Implement Gemini improver with same interface
- [ ] Test quality on 20-30 real resumes (Claude vs Gemini)
- [ ] Measure cost per resume for both
- [ ] If quality ≥90% equivalent, swap in improve.py
- [ ] Keep retry logic and error handling
- [ ] Remove anthropic dependency if fully migrated

**Quality Test Checklist:**
- [ ] Bullet points have action verbs
- [ ] Metrics/numbers preserved
- [ ] No hallucination of achievements
- [ ] Professional tone maintained
- [ ] Response time <5s per improvement

#### 1.3 Build Internal Resume Parser
**Files to create:**
- `app/services/parser.py` - PyMuPDF + spaCy parser

**Tasks:**
- [ ] Extract text from PDF using PyMuPDF
- [ ] Extract text from DOCX using python-docx
- [ ] Use spaCy for entity recognition (names, emails, phones)
- [ ] Section detection (Experience, Education, Skills, Summary)
- [ ] Structured data extraction (dates, companies, titles)
- [ ] Add fallback to external parser if internal fails
- [ ] Test with 50+ diverse resume formats

**Expected Output Schema:**
```python
{
    "name": str,
    "email": str,
    "phone": str,
    "sections": {
        "summary": str,
        "experience": [{"title": str, "company": str, "dates": str, "bullets": [str]}],
        "education": [{"degree": str, "institution": str, "year": str}],
        "skills": [str]
    },
    "raw_text": str
}
```

---

### Phase 2: Production Hardening (Days 4-5)

#### 2.1 Job Persistence & Database
**Files to create:**
- `supabase/migrations/001_jobs_table.sql` - Job tracking table
- `app/services/database.py` - Database operations

**Files to modify:**
- `app/routers/analyze.py` - Save job to DB
- `app/worker.py` - Update job status in DB

**Tasks:**
- [ ] Create Supabase tables for jobs
- [ ] Implement job creation in DB
- [ ] Update status endpoint to query DB
- [ ] Add job expiration (30 days) with cleanup
- [ ] Store error logs and retry attempts
- [ ] Add indexes for performance

**Database Schema:**
```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT,
  job_type TEXT NOT NULL, -- analyze, improve, generate
  status TEXT NOT NULL, -- queued, processing, completed, failed
  input_data JSONB,
  result JSONB,
  error TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  retry_count INTEGER DEFAULT 0
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
```

#### 2.2 Complete TODOs
**Files to modify:**
- `app/routers/analyze.py:61` - Implement real status endpoint
- `app/routers/improve.py:83` - Implement apply improvements tracking
- `app/routers/generate.py:92` - Implement regenerate with DB fetch
- `app/services/improver.py:157` - Implement keyword suggestions

**Tasks:**
- [ ] Status endpoint queries job from DB
- [ ] Apply improvements stores user selections
- [ ] Regenerate fetches original content from DB
- [ ] Keyword suggestion uses VA_KEYWORDS list

#### 2.3 Logging & Error Handling
**Files to create:**
- `app/utils/logging.py` - Structured logging setup

**Files to modify:**
- `app/main.py` - Initialize logging
- All services - Add structured logs

**Tasks:**
- [ ] Add `structlog` to requirements
- [ ] Configure JSON logging for Railway
- [ ] Log all LLM calls with token counts and costs
- [ ] Add error tracking (Sentry optional)
- [ ] Implement graceful degradation for failures
- [ ] Add retry logic to storage operations

---

### Phase 3: Infrastructure (Day 6)

#### 3.1 Railway Deployment Configuration
**Files to create:**
- `railway.toml` - Multi-service deployment config
- `.env.example` - Environment variable template
- `scripts/validate_env.py` - Startup validation

**Files to modify:**
- `Dockerfile` - Conditional startup (API vs Worker)

**Tasks:**
- [ ] Create railway.toml with two services
- [ ] Update Dockerfile with WORKER_MODE env check
- [ ] Create comprehensive .env.example
- [ ] Add environment validation on startup
- [ ] Test deployment to Railway
- [ ] Verify worker and API both start correctly

**railway.toml:**
```toml
[build]
builder = "dockerfile"

[[services]]
name = "api-gateway"
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
env = { WORKER_MODE = "false" }

[[services]]
name = "job-worker"
startCommand = "arq app.worker.WorkerSettings"
env = { WORKER_MODE = "true" }
```

#### 3.2 Local Development Setup
**Files to create:**
- `docker-compose.yml` - Local development stack
- `Makefile` - Common development commands
- `scripts/setup_local.sh` - First-time setup script

**Tasks:**
- [ ] Create docker-compose with API, Worker, Redis
- [ ] Add make commands (dev, test, migrate, etc.)
- [ ] Update README with setup instructions
- [ ] Test local development flow
- [ ] Document common issues and solutions

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    environment:
      - WORKER_MODE=false
      - REDIS_URL=redis://redis:6379
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app

  worker:
    build: .
    environment:
      - WORKER_MODE=true
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
```

---

### Phase 4: Testing & Optimization (Day 7)

#### 4.1 Integration Testing
**Files to create:**
- `tests/integration/test_job_flow.py` - End-to-end tests
- `tests/integration/test_failures.py` - Failure scenarios
- `tests/load/test_concurrent.py` - Load testing

**Tasks:**
- [ ] Test complete job flow: upload → analyze → improve → generate
- [ ] Test corrupt PDF handling
- [ ] Test LLM timeout scenarios
- [ ] Test storage failures
- [ ] Load test: 100 concurrent job submissions
- [ ] Verify cost per resume <$0.01
- [ ] Test job status polling
- [ ] Test job expiration and cleanup

#### 4.2 Cost Optimization
**Files to modify:**
- `app/services/gemini_improver.py` - Optimize prompts

**Tasks:**
- [ ] Reduce prompt token count (remove examples if possible)
- [ ] Cache identical improvement requests
- [ ] Batch similar operations
- [ ] Monitor actual cost per resume
- [ ] Set up cost alerts if exceeds threshold

---

## 📦 Deliverables Checklist

### New Files
- [ ] `app/worker.py` - ARQ worker implementation
- [ ] `app/services/queue.py` - Job queue management
- [ ] `app/services/parser.py` - Internal resume parser
- [ ] `app/services/gemini_improver.py` - Gemini integration
- [ ] `app/services/database.py` - Database operations
- [ ] `app/utils/logging.py` - Structured logging
- [ ] `railway.toml` - Railway config
- [ ] `docker-compose.yml` - Local dev stack
- [ ] `.env.example` - Environment template
- [ ] `Makefile` - Dev commands
- [ ] `supabase/migrations/001_jobs_table.sql` - Jobs table
- [ ] `scripts/test_gemini_quality.py` - Quality testing
- [ ] `scripts/validate_env.py` - Environment validation
- [ ] `scripts/setup_local.sh` - Setup script
- [ ] `tests/integration/test_job_flow.py` - Integration tests

### Modified Files
- [ ] `requirements.txt` - Add arq, redis, google-generativeai, structlog
- [ ] `app/main.py` - Initialize logging, remove worker code
- [ ] `app/routers/analyze.py` - Convert to async pattern
- [ ] `app/routers/improve.py` - Convert to async, swap to Gemini
- [ ] `app/routers/generate.py` - Convert to async pattern
- [ ] `app/utils/config.py` - Add Redis, Gemini, logging config
- [ ] `Dockerfile` - Conditional worker/API startup
- [ ] `README.md` - Update setup instructions

### Infrastructure
- [ ] Railway Redis service provisioned
- [ ] Railway API service deployed
- [ ] Railway Worker service deployed
- [ ] Supabase jobs table created
- [ ] Environment variables configured
- [ ] Logging/monitoring configured

---

## 🎬 Execution Order

### Day 1: Job Queue Foundation
1. ✅ Set up Redis on Railway
2. ✅ Create app/worker.py with basic structure
3. ✅ Create app/services/queue.py
4. ✅ Update config.py with Redis settings
5. ✅ Test Redis connection and basic job enqueueing

### Day 2: Async Endpoint Migration
1. ✅ Convert analyze endpoint to async pattern
2. ✅ Convert improve endpoint to async pattern
3. ✅ Convert generate endpoint to async pattern
4. ✅ Implement status and result endpoints
5. ✅ Test full job flow with Postman/curl

### Day 3: Gemini Migration + Parser
1. ✅ Implement Gemini improver
2. ✅ Test Gemini quality vs Claude
3. ✅ Swap if quality acceptable
4. ✅ Build internal parser with PyMuPDF
5. ✅ Test parser with diverse resumes

### Day 4: Database + TODOs
1. ✅ Create Supabase migrations
2. ✅ Implement database.py
3. ✅ Update endpoints to use DB
4. ✅ Complete all TODO items
5. ✅ Add structured logging

### Day 5: Infrastructure
1. ✅ Create railway.toml
2. ✅ Update Dockerfile
3. ✅ Create docker-compose.yml
4. ✅ Test local development setup
5. ✅ Deploy to Railway with worker

### Day 6: Testing
1. ✅ Write integration tests
2. ✅ Load test with 100 concurrent jobs
3. ✅ Test failure scenarios
4. ✅ Verify cost per resume
5. ✅ Fix any bugs found

### Day 7: Documentation + Cleanup
1. ✅ Update README
2. ✅ Create .env.example
3. ✅ Write setup scripts
4. ✅ Document API changes
5. ✅ Final deployment verification

---

## 📊 Success Metrics

### Performance
- ✅ API response time <200ms (job submission)
- ✅ Status endpoint <100ms
- ✅ Job completion within 30-60s
- ✅ 99% job success rate
- ✅ Handle 100 concurrent requests

### Cost (per 1,000 resumes)
- ✅ AI: <$0.50 (Gemini)
- ✅ Infrastructure: <$0.02
- ✅ Total: <$0.52 per 1,000 resumes
- ✅ **Target:** <$0.001 per resume

### Reliability
- ✅ Zero external parser dependencies
- ✅ Automatic retry on transient failures
- ✅ Job persistence across restarts
- ✅ Graceful degradation on errors

### Developer Experience
- ✅ Local dev setup in <5 minutes
- ✅ Clear error messages
- ✅ Comprehensive logging
- ✅ Easy deployment process

---

## 💡 Future Enhancements (Post-MVP)

### Features
- DOCX output format (premium feature)
- Batch processing API
- Webhook notifications on job completion
- Resume comparison/versioning
- Industry-specific optimizations
- Multi-language support

### Technical
- Response caching (Redis)
- Rate limiting per user
- Analytics dashboard
- A/B testing framework for prompts
- GraphQL API
- WebSocket for real-time status

### Business
- Usage tracking and billing
- User accounts and authentication
- Template marketplace
- API key management
- SLA monitoring

---

## 🚨 Risk Mitigation

### Gemini Quality Risk
- **Risk:** Gemini output quality lower than Claude
- **Mitigation:** Test on 30+ resumes before migration, keep Claude as fallback option, implement A/B testing

### Job Queue Complexity
- **Risk:** ARQ adds complexity, bugs in async code
- **Mitigation:** Comprehensive integration tests, start with simple jobs, add complexity incrementally

### Cost Overruns
- **Risk:** Usage exceeds projections
- **Mitigation:** Set up cost alerts, implement rate limiting, monitor token usage per request

### External Parser Dependency
- **Risk:** Current external parser may fail
- **Mitigation:** Build internal parser first, use external as fallback only during transition

---

## 📞 Support & Resources

### Documentation
- [ARQ Documentation](https://arq-docs.helpmanual.io/)
- [Gemini API Docs](https://ai.google.dev/docs)
- [Railway Docs](https://docs.railway.app/)
- [Supabase Storage](https://supabase.com/docs/guides/storage)

### Tools
- Postman collection for API testing
- Sample resumes for quality testing
- Load testing scripts
- Cost calculator spreadsheet

---

## ✅ Getting Started Checklist

Before you begin implementation:

- [ ] Review this plan thoroughly
- [ ] Ensure Railway account has Redis addon available
- [ ] Confirm Gemini API access and quota
- [ ] Back up current production database
- [ ] Create feature branch: `feature/async-migration`
- [ ] Set up local Redis for development
- [ ] Download 20-30 sample resumes for testing
- [ ] Communicate migration timeline to stakeholders

---

**Document Version:** 1.0
**Last Updated:** 2025-11-19
**Estimated Total Effort:** 7-10 engineering days
**Expected ROI:** <1 month payback at 5,000 resumes/month
