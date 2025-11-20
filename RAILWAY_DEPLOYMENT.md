# Railway Deployment Guide - Resume Engine v2.0

## 🚀 Quick Deploy to Railway

### Prerequisites
- ✅ Railway account with Redis already provisioned
- ✅ Redis URL: `redis://default:sqjoLRhgsdDHCuVTHcjYLtjATJNUsIyy@redis.railway.internal:6379`
- ✅ All environment variables ready (in your `.env` file)

---

## Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Add async job queue with ARQ + Redis"

# Push to GitHub (create repo first on github.com)
git remote add origin https://github.com/YOUR_USERNAME/resume-improvement-api.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Railway

### Option A: Using Railway CLI (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Deploy
railway up
```

### Option B: Using Railway Dashboard

1. Go to [railway.app](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Select your `resume-improvement-api` repository
5. Railway will auto-detect the `railway.toml` and create **TWO services**:
   - `resume-api` (API Gateway)
   - `resume-worker` (Background Worker)

---

## Step 3: Configure Environment Variables

Railway will need these environment variables set for **BOTH services**:

### For API Service (`resume-api`):

```bash
# API Configuration
API_KEY=your-secure-api-key-from-env-file
ENVIRONMENT=production

# Supabase (copy from your .env file)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# AI Services (copy from your .env file)
ANTHROPIC_API_KEY=your-anthropic-api-key
GEMINI_API_KEY=your-gemini-api-key

# Redis (automatically set by Railway, but verify)
REDIS_URL=${{Redis.REDIS_URL}}

# Worker Mode
WORKER_MODE=false

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# Logging
LOG_LEVEL=INFO
```

### For Worker Service (`resume-worker`):

Same as above, but change:
```bash
WORKER_MODE=true
```

**Note:** Railway automatically provides `${{Redis.REDIS_URL}}` if you've linked the Redis service.

---

## Step 4: Verify Deployment

### Check Services Are Running

In Railway dashboard, you should see:
- ✅ `resume-api` - Status: **Running** (green)
- ✅ `resume-worker` - Status: **Running** (green)
- ✅ `Redis` - Status: **Running** (green)

### Get Your API URL

Railway will provide a public URL for your API service:
```
https://resume-api-production-xxxx.up.railway.app
```

---

## Step 5: Test the API

### Test Health Endpoint

```bash
curl https://YOUR-RAILWAY-URL.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T12:00:00Z"
}
```

### Test Async Job Flow

```bash
# 1. Submit a job (should return instantly)
curl -X POST https://YOUR-RAILWAY-URL.railway.app/api/v1/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://example.com/test-resume.pdf",
    "user_id": "test-user"
  }'
```

Expected response (instant):
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "status_url": "/api/v1/analyze/status/550e8400-e29b-41d4-a716-446655440000",
  "result_url": "/api/v1/analyze/result/550e8400-e29b-41d4-a716-446655440000",
  "eta_seconds": 30,
  "message": "Analysis job queued. Poll status_url for updates."
}
```

### Check Job Status

```bash
# 2. Check status (use the job_id from above)
curl https://YOUR-RAILWAY-URL.railway.app/api/v1/analyze/status/YOUR-JOB-ID \
  -H "X-API-Key: YOUR_API_KEY"
```

Status progression:
- `queued` → Job waiting in Redis
- `in_progress` → Worker processing
- `complete` → Job done, result available
- `failed` → Job failed (check error message)

### Get Result

```bash
# 3. Get result once status is "complete"
curl https://YOUR-RAILWAY-URL.railway.app/api/v1/analyze/result/YOUR-JOB-ID \
  -H "X-API-Key: YOUR_API_KEY"
```

---

## Step 6: Monitor Logs

### View Logs in Railway Dashboard

1. Go to your project in Railway
2. Click on `resume-api` service → **Logs** tab
3. Click on `resume-worker` service → **Logs** tab

### What to Look For

**API Logs (resume-api):**
```
🚀 Resume Improvement API starting up...
✅ spaCy model loaded successfully
INFO: Started server process
INFO: Uvicorn running on http://0.0.0.0:8000
```

**Worker Logs (resume-worker):**
```
🚀 ARQ Worker starting up...
Environment: production
Max concurrent jobs: 10
Job timeout: 300s
✅ spaCy model loaded successfully
```

**When a job runs:**
```
[Job 550e8400-...] Starting resume analysis for https://...
[Job 550e8400-...] Analysis complete. Overall score: 72.5
```

---

## Troubleshooting

### Issue: Services won't start

**Check:**
1. All environment variables are set correctly
2. Redis service is running and linked
3. Check logs for specific errors

### Issue: Jobs stay in "queued" status

**Likely cause:** Worker not running or not connected to Redis

**Fix:**
1. Check `resume-worker` service is running
2. Verify `REDIS_URL` is set correctly
3. Check worker logs for connection errors

### Issue: "Job not found" error

**Likely cause:** Job ID expired (ARQ keeps results for 1 hour by default)

**Fix:**
- Jobs are cleaned up after 1 hour
- For production, implement database persistence (Day 4)

### Issue: 401 Unauthorized

**Fix:** Make sure you're sending the correct API key in the `X-API-Key` header

---

## Architecture on Railway

```
┌─────────────────────────────────────────┐
│           Railway Project               │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────┐                     │
│  │  resume-api   │  (FastAPI)          │
│  │  Port: 8000   │                     │
│  │  Public URL   │                     │
│  └───────┬───────┘                     │
│          │                              │
│          │  Enqueues Jobs              │
│          ↓                              │
│  ┌───────────────┐                     │
│  │     Redis     │  (Job Queue)        │
│  │  Internal URL │                     │
│  └───────┬───────┘                     │
│          │                              │
│          │  Dequeues Jobs              │
│          ↓                              │
│  ┌───────────────┐                     │
│  │ resume-worker │  (ARQ Worker)       │
│  │  Background   │                     │
│  │  Processing   │                     │
│  └───────────────┘                     │
│                                         │
└─────────────────────────────────────────┘
```

---

## Cost Estimate

Based on current Railway pricing:

| Service | Cost | Notes |
|---------|------|-------|
| API Service | ~$5-10/mo | Shared compute |
| Worker Service | ~$5-10/mo | Shared compute |
| Redis | $5/mo | Small instance |
| **Total** | **~$15-25/mo** | Scales with usage |

At 5,000 resumes/month with Claude:
- Infrastructure: $20/mo
- Claude API: $105/mo (5k × $21/1000)
- **Total: $125/mo**

*Note: Migrating to Gemini (Day 3) would reduce AI cost to $2.25/mo*

---

## Next Steps After Deployment

1. ✅ **Test the async job flow** - Make sure jobs complete successfully
2. ⏳ **Add database persistence** - Store jobs in Supabase (Day 4)
3. ⏳ **Migrate to Gemini** - Reduce costs by 47x (Day 3)
4. ⏳ **Add monitoring** - Set up alerts for failures
5. ⏳ **Load testing** - Test with 100 concurrent jobs

---

## Support

- **Logs:** Check Railway dashboard logs for both services
- **Status:** Monitor job completion rates
- **Errors:** Check worker logs for job failures

**Ready to deploy?** Follow the steps above and let me know if you hit any issues!
