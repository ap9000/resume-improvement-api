# Railway Testing Deployment Guide

## Current Status: **READY FOR TESTING** ✅

Docker health check has been fixed! You can now deploy to Railway for testing.

---

## ✅ What's Ready

- Resume analysis (all 5 scoring algorithms)
- Claude AI improvements (async with retry)
- Rate limiting (cost protection)
- Storage with signed URLs
- Database schema
- Docker configuration **FIXED**

## ⚠️ What Won't Work Yet

- PDF generation (no HTML templates)
- Full end-to-end flow (missing templates)

**But you can test:** Analysis, improvements, rate limiting, storage, auth

---

## 🚀 Deploy to Railway (15 minutes)

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Create New Project

```bash
cd resume-improvement-api
railway init

# Choose:
# - "Empty Project"
# - Name: "resume-improvement-api-test"
```

### Step 3: Set Environment Variables

**Option A: Via CLI** (Recommended)

```bash
# API Configuration
railway variables set API_KEY="your-secure-random-key-here"
railway variables set ENVIRONMENT="staging"

# Supabase (from your main project)
railway variables set SUPABASE_URL="https://your-project.supabase.co"
railway variables set SUPABASE_ANON_KEY="your-anon-key"
railway variables set SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Claude API
railway variables set ANTHROPIC_API_KEY="sk-ant-api03-..."

# Optional: Resume Parser API
railway variables set VITE_RESUME_PARSER_API_URL="https://your-parser.railway.app"
railway variables set VITE_RESUME_PARSER_API_KEY="your-parser-key"

# Rate Limiting
railway variables set RATE_LIMIT_PER_MINUTE="10"
railway variables set RATE_LIMIT_PER_HOUR="100"

# CORS (add your frontend URL)
railway variables set CORS_ORIGINS="http://localhost:8080,https://your-frontend.com"

# Logging
railway variables set LOG_LEVEL="INFO"
```

**Option B: Via Dashboard**

1. Go to https://railway.app/dashboard
2. Select your project
3. Click "Variables"
4. Add all variables from above

### Step 4: Deploy

```bash
railway up
```

This will:
1. Build Docker image (takes 5-10 minutes first time)
2. Download spaCy models
3. Install all dependencies
4. Start the API
5. Run health checks

**Watch the build logs:**
```bash
railway logs
```

### Step 5: Get Your URL

```bash
railway domain
```

Or in dashboard: Project → Deployments → Public URL

Example: `https://resume-improvement-api-test.up.railway.app`

### Step 6: Test the Deployment

```bash
# Save your Railway URL
export RAILWAY_URL="https://your-app.up.railway.app"

# Test health check
curl $RAILWAY_URL/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": 1234567890,
#   "services": {"nlp": true}
# }

# Test templates (no auth required)
curl $RAILWAY_URL/api/v1/templates

# Test with authentication
curl -X POST $RAILWAY_URL/api/v1/analyze \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://your-supabase.co/storage/v1/object/public/profiles/resumes/test.pdf",
    "user_id": "test-123"
  }'
```

---

## 📊 Monitoring Your Deployment

### View Logs

```bash
# Real-time logs
railway logs

# Filter errors
railway logs | grep ERROR

# Filter by service
railway logs --service resume-improvement-api-test
```

### Check Metrics

In Railway Dashboard:
- **Deployments** → Your deployment → Metrics
- Monitor: CPU, Memory, Network

### Health Checks

Railway will automatically:
- Check `/health` every 30 seconds
- Restart if unhealthy 3 times
- Show status in dashboard

---

## 🧪 What to Test

### 1. **Health & Readiness**

```bash
# Health check
curl https://your-app.railway.app/health

# Readiness check
curl https://your-app.railway.app/ready
```

**Expected**: Both return 200 with healthy status

### 2. **API Documentation**

Visit: `https://your-app.railway.app/docs`

**Expected**: Interactive Swagger UI

### 3. **Authentication**

```bash
# Without API key (should fail)
curl https://your-app.railway.app/api/v1/templates

# With API key (should succeed)
curl -H "X-API-Key: your-key" https://your-app.railway.app/api/v1/templates
```

### 4. **Rate Limiting**

```bash
# Send 6 rapid requests (limit is 5/minute)
for i in {1..6}; do
  curl -X POST https://your-app.railway.app/api/v1/analyze \
    -H "X-API-Key: your-key" \
    -H "Content-Type: application/json" \
    -d '{"resume_url": "test.pdf", "user_id": "test"}' \
    -w "\nStatus: %{http_code}\n"
done
```

**Expected**: First 5 succeed, 6th returns 429 (rate limit exceeded)

### 5. **Resume Analysis** (If parser API available)

```bash
curl -X POST https://your-app.railway.app/api/v1/analyze \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://your-supabase.co/storage/.../resume.pdf",
    "user_id": "test-user",
    "resume_improvement_id": "test-123"
  }'
```

**Expected**: Returns scores, issues, suggestions

### 6. **Claude AI Improvements**

```bash
curl -X POST https://your-app.railway.app/api/v1/improve \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_improvement_id": "test-123",
    "content": {
      "experience": [
        {
          "role": "Virtual Assistant",
          "company": "Test Corp",
          "responsibilities": ["Managed emails"]
        }
      ]
    },
    "focus_areas": ["bullet_points"]
  }'
```

**Expected**: Claude rewrites bullet point with improvements

### 7. **PDF Generation** (Will Fail - Expected!)

```bash
curl -X POST https://your-app.railway.app/api/v1/generate \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Expected Error**: `TemplateNotFound: modern.html`

**This is normal** - we haven't created templates yet.

---

## 🐛 Troubleshooting

### Build Fails

**Issue**: "Dockerfile not found"
```bash
# Ensure you're in the right directory
cd resume-improvement-api
railway up
```

**Issue**: "Port 8000 already in use"
- Railway automatically sets the PORT env var
- Dockerfile is configured correctly
- Restart deployment if needed

### Runtime Issues

**Issue**: "NLP model not loaded"
```bash
# Check build logs
railway logs | grep spacy

# Should see: "spaCy model loaded successfully"
```

**Issue**: "Connection to Supabase failed"
- Verify SUPABASE_URL in Railway variables
- Check service role key is correct
- Test URL in browser

**Issue**: "Claude API error"
- Verify ANTHROPIC_API_KEY in Railway variables
- Check you have API credits at console.anthropic.com
- Look for specific error in logs

### Health Check Fails

```bash
# Check health endpoint directly
curl https://your-app.railway.app/health

# Check logs for errors
railway logs | grep ERROR

# Common issues:
# - spaCy model not downloaded
# - Environment variables missing
# - Port not correctly set
```

---

## 💰 Cost Estimates

### Railway Pricing

**Free Tier:**
- $5 credit per month
- Good for testing
- May need to upgrade for production

**Hobby Plan: $5/month**
- Enough for low-traffic testing
- No credit card required initially

**Pro Plan: $20/month**
- Recommended for production
- Better resource limits

### Expected Usage

**For Testing:**
- ~10-20 API calls/day
- ~$0.50/day Claude API
- **Total: ~$1-2/day**

**For Production:**
- Depends on traffic
- Rate limiting protects costs
- Max ~$2.70/hour with limits

---

## 📋 Post-Deployment Checklist

- [ ] Health check returns 200
- [ ] Readiness check returns 200
- [ ] API docs accessible at `/docs`
- [ ] Authentication works (API key required)
- [ ] Rate limiting enforced (6th request fails)
- [ ] Templates endpoint works
- [ ] (Optional) Analysis endpoint with real resume
- [ ] (Optional) Claude improvements work
- [ ] Environment variables all set
- [ ] Logs show no errors
- [ ] Database migration ran successfully

---

## 🔄 Updating the Deployment

### After Code Changes

```bash
# Deploy new version
railway up

# Watch deployment
railway logs
```

### Update Environment Variables

```bash
# Update a variable
railway variables set API_KEY="new-key"

# Restart deployment
railway restart
```

### Rollback if Needed

```bash
# View deployments
railway status

# Rollback to previous
railway rollback
```

---

## 🎯 What You Can Validate in Testing

| Feature | Can Test? | Notes |
|---------|-----------|-------|
| Health checks | ✅ Yes | Should return healthy |
| API authentication | ✅ Yes | X-API-Key required |
| Rate limiting | ✅ Yes | 5/min for analyze |
| Resume analysis | ⚠️ Partial | Needs parser API |
| Claude improvements | ✅ Yes | Needs Claude key |
| PDF generation | ❌ No | No templates yet |
| Storage upload | ✅ Yes | If Supabase configured |
| Signed URLs | ✅ Yes | Returns 1-hour URLs |
| Error handling | ✅ Yes | Graceful failures |
| Async performance | ✅ Yes | Non-blocking |

---

## 🚀 Next Steps After Testing

Once Railway testing is successful:

1. **Create HTML templates** (2-3 days)
   - Enables PDF generation
   - Completes the flow

2. **Write tests** (5 days)
   - Unit tests for scoring
   - Integration tests for API
   - Load tests for performance

3. **Add monitoring** (2 days)
   - Sentry for error tracking
   - Structured logging
   - Metrics dashboard

4. **Production deployment** (1 week)
   - Custom domain
   - CDN setup
   - Full load testing
   - Go-live!

---

## 📞 Support

**If you encounter issues:**

1. Check logs: `railway logs`
2. Verify environment variables in dashboard
3. Test health endpoint directly
4. Check Supabase connection
5. Verify Claude API key and credits

**Common Solutions:**
- Restart deployment: `railway restart`
- Redeploy: `railway up`
- Check Railway status: https://railway.app/status
- View build logs in dashboard

---

## Summary

**Can Deploy Now?** ✅ YES

**What Works:**
- Core analysis functionality
- AI improvements
- Rate limiting
- Storage security
- Authentication
- Error handling

**What Doesn't:**
- PDF generation (no templates)

**Recommended:**
1. Deploy to Railway for testing
2. Test all working endpoints
3. Verify rate limiting
4. Check Claude API integration
5. Create templates next
6. Deploy updated version
7. Full end-to-end testing

**Estimated time to deploy:** 15-30 minutes

**Ready to deploy? Run:**
```bash
cd resume-improvement-api
railway login
railway init
railway variables set ... # (all env vars)
railway up
```

🚀 Good luck with testing!
