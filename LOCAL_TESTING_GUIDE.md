# Local Testing Guide - Resume Improvement API

## Prerequisites

- Python 3.11+
- Virtual environment tool (venv)
- Access to Supabase project
- Anthropic API key
- Existing resume parser API running (optional for full test)

---

## Quick Start (5 minutes)

### 1. Install Dependencies

```bash
cd resume-improvement-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLP model
python -m spacy download en_core_web_sm

# Download NLTK data (for text analysis)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### 2. Configure Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# API Configuration
API_KEY=test-api-key-12345  # Use any string for local testing

# Supabase (from your main project)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Claude API (get from https://console.anthropic.com/)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional: Resume Parser API (if you have it running)
VITE_RESUME_PARSER_API_URL=https://your-parser.railway.app
VITE_RESUME_PARSER_API_KEY=your-parser-key

# Rate Limiting (good defaults for local testing)
RATE_LIMIT_PER_MINUTE=100  # Higher for local testing
RATE_LIMIT_PER_HOUR=1000

# CORS (allow localhost)
CORS_ORIGINS=http://localhost:8080,http://localhost:5173

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### 3. Run Database Migration

```bash
# In Supabase SQL Editor, run:
# 1. supabase/migrations/20251112000000_create_resume_improvement_tables.sql
# 2. database/setup_resume_improvements_storage.sql
```

Or using Supabase CLI:
```bash
supabase db push
```

### 4. Start the API

```bash
# Make sure you're in the resume-improvement-api directory
# and virtual environment is activated

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 5. Test the API

Open browser: http://localhost:8000/docs

You'll see the FastAPI interactive documentation (Swagger UI).

---

## What You Can Test Now

### ✅ **Working Endpoints:**

#### 1. Health Check (No auth required)
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "services": {
    "nlp": true
  }
}
```

#### 2. Templates List (No auth required)
```bash
curl http://localhost:8000/api/v1/templates
```

Expected response:
```json
{
  "success": true,
  "templates": [
    {
      "id": "modern",
      "name": "Modern",
      "description": "Clean, minimal design...",
      "best_for": ["Tech-savvy VAs", ...]
    },
    ...
  ]
}
```

#### 3. Resume Analysis (Requires auth + resume URL)

**Note**: This will work IF you have:
- A resume uploaded to Supabase storage OR
- The Railway parser API running

```bash
# Using curl
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://your-project.supabase.co/storage/v1/object/public/profiles/resumes/test.pdf",
    "user_id": "test-user-123",
    "resume_improvement_id": "test-session-123"
  }'
```

**Expected response** (if parser works):
```json
{
  "success": true,
  "resume_improvement_id": "test-session-123",
  "scores": {
    "overall_score": 72.5,
    "formatting_score": 15.0,
    "content_quality_score": 20.0,
    ...
  },
  "issues": [...],
  "suggestions": [...],
  "metadata": {...}
}
```

#### 4. AI Improvements (Requires Claude API key)

```bash
curl -X POST http://localhost:8000/api/v1/improve \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_improvement_id": "test-123",
    "content": {
      "title": "Virtual Assistant",
      "experience": [
        {
          "role": "VA",
          "company": "Test Corp",
          "bullets": ["Managed calendars"]
        }
      ],
      "skills": ["Email", "Calendar"]
    },
    "focus_areas": ["bullet_points"]
  }'
```

Expected: Claude will rewrite the bullet point with better content.

### ⚠️ **Will Fail (Expected):**

#### 5. PDF Generation
```bash
# This WILL FAIL - no templates exist yet
curl -X POST http://localhost:8000/api/v1/generate \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

Error:
```
TemplateNotFound: modern.html
```

**Why**: We haven't created the HTML templates yet.

---

## Testing Without Resume Parser

If you don't have the resume parser API running, you can test with mock data:

**Option 1**: Use Swagger UI (http://localhost:8000/docs)
- Click "Try it out" on any endpoint
- Fill in the request body
- See live responses

**Option 2**: Create a test script

Create `test_local.py`:

```python
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-12345"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Test health
response = requests.get(f"{BASE_URL}/health")
print(f"Health: {response.json()}")

# Test templates
response = requests.get(f"{BASE_URL}/api/v1/templates")
print(f"Templates: {response.json()}")

# Test analysis (will fail without parser, but tests auth + validation)
response = requests.post(
    f"{BASE_URL}/api/v1/analyze",
    headers=headers,
    json={
        "resume_url": "https://test.com/resume.pdf",
        "user_id": "test-123"
    }
)
print(f"Analysis: {response.status_code} - {response.text}")
```

Run:
```bash
python test_local.py
```

---

## Testing Rate Limiting

```bash
# Send 6 requests quickly (limit is 5/minute for analyze)
for i in {1..6}; do
  echo "Request $i"
  curl -X POST http://localhost:8000/api/v1/analyze \
    -H "X-API-Key: test-api-key-12345" \
    -H "Content-Type: application/json" \
    -d '{"resume_url": "test.pdf", "user_id": "test"}' \
    -w "\nStatus: %{http_code}\n\n"
  sleep 1
done
```

**Expected**: First 5 succeed, 6th returns:
```json
{
  "error": "Rate limit exceeded",
  "detail": "5 per 1 minute"
}
```

---

## Troubleshooting

### Issue: "Module not found"
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### Issue: "Connection to Supabase failed"
- Check `.env` file has correct SUPABASE_URL
- Verify service role key is correct
- Test connection in browser: `https://your-project.supabase.co`

### Issue: "Claude API error"
- Check ANTHROPIC_API_KEY in `.env`
- Verify key at https://console.anthropic.com/
- Check you have credits available

### Issue: "Resume parsing failed"
- This is expected if parser API isn't running
- You can still test other endpoints (health, templates, improvements)

### Issue: "Port 8000 already in use"
```bash
# Use different port
uvicorn app.main:app --reload --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

---

## What Works vs What Doesn't

| Feature | Status | Notes |
|---------|--------|-------|
| **Health Check** | ✅ Works | No dependencies |
| **Templates List** | ✅ Works | Returns metadata |
| **Rate Limiting** | ✅ Works | Test with rapid requests |
| **API Authentication** | ✅ Works | X-API-Key header |
| **Resume Analysis** | ⚠️ Partial | Needs parser API OR resume in storage |
| **AI Improvements** | ✅ Works | Needs Claude API key |
| **PDF Generation** | ❌ Fails | No templates yet |
| **Storage Upload** | ✅ Works | If Supabase configured |
| **Signed URLs** | ✅ Works | If Supabase configured |

---

## Recommended Test Flow

**5-Minute Quick Test:**
1. Start API: `uvicorn app.main:app --reload`
2. Open browser: http://localhost:8000/docs
3. Test `/health` - Should return healthy
4. Test `/api/v1/templates` - Should list 4 templates
5. Try `/api/v1/analyze` - Will fail without resume, but tests validation

**Full Test (30 minutes):**
1. Upload a test resume to Supabase storage
2. Run database migrations
3. Configure all environment variables
4. Test analysis endpoint with real resume
5. Test improvement endpoint with Claude
6. Verify rate limiting works
7. Check logs for errors

---

## Next Steps After Local Testing

Once local testing works:

1. **Create HTML templates** (needed for PDF generation)
2. **Write unit tests** (for reliability)
3. **Fix Docker issues** (for deployment)
4. **Deploy to Railway** (for production testing)

---

## Local Testing Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] spaCy model downloaded
- [ ] `.env` file created with all keys
- [ ] Database migrations run
- [ ] API starts without errors
- [ ] Health check returns 200
- [ ] Templates endpoint works
- [ ] Rate limiting tested
- [ ] (Optional) Full analysis with resume tested
- [ ] (Optional) Claude improvements tested

---

**Ready to start? Run these commands:**

```bash
cd resume-improvement-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env
# Edit .env with your keys
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs 🚀
