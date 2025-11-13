# Deployment Guide - Resume Improvement API

Complete guide to deploying the Resume Improvement API to Railway.

## Pre-Deployment Checklist

### 1. Prepare Supabase

- [ ] Run database migration: `20251112000000_create_resume_improvement_tables.sql`
- [ ] Run storage setup: `database/setup_resume_improvements_storage.sql`
- [ ] Verify tables created: `resume_improvements`, `resume_analyses`, `improved_resumes`
- [ ] Verify storage bucket created: `resume-improvements`
- [ ] Test RLS policies with a test user

### 2. Get API Keys

- [ ] Anthropic API key from https://console.anthropic.com/
- [ ] Supabase anon key (Project Settings > API)
- [ ] Supabase service role key (Project Settings > API)
- [ ] Generate secure API key for your frontend to use

### 3. Test Locally

```bash
cd resume-improvement-api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Create .env file
cp .env.example .env
# Edit .env with your keys

# Run server
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/health
```

## Railway Deployment

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Create New Project

```bash
cd resume-improvement-api
railway init
# Choose "Empty Project"
# Name it: resume-improvement-api
```

### Step 3: Add Environment Variables

**Option A: Via CLI**
```bash
railway variables set API_KEY="your-secure-api-key-here"
railway variables set ENVIRONMENT="production"
railway variables set SUPABASE_URL="https://your-project.supabase.co"
railway variables set SUPABASE_ANON_KEY="your-anon-key"
railway variables set SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
railway variables set ANTHROPIC_API_KEY="your-anthropic-key"
railway variables set RATE_LIMIT_PER_MINUTE="10"
railway variables set RATE_LIMIT_PER_HOUR="100"
railway variables set MAX_FILE_SIZE_MB="5"
railway variables set LOG_LEVEL="INFO"
```

**Option B: Via Railway Dashboard**
1. Go to https://railway.app/dashboard
2. Select your project
3. Click "Variables"
4. Add each variable from above

### Step 4: Deploy

```bash
# Deploy the API
railway up

# Watch logs
railway logs

# Get deployment URL
railway domain
```

### Step 5: Configure Custom Domain (Optional)

```bash
# Add custom domain
railway domain add api.yourcompany.com

# Update DNS:
# Type: CNAME
# Name: api
# Value: [railway-url].up.railway.app
```

### Step 6: Verify Deployment

```bash
# Get your Railway URL
RAILWAY_URL=$(railway domain)

# Test health endpoint
curl https://$RAILWAY_URL/health

# Test with API key
curl -H "X-API-Key: your-api-key" https://$RAILWAY_URL/api/v1/templates

# Visit docs
open https://$RAILWAY_URL/docs
```

## Update Frontend Environment Variables

Add to your main app's `.env`:

```bash
# In vamarketplacenew/.env
VITE_RESUME_IMPROVEMENT_API_URL=https://your-api.up.railway.app
VITE_RESUME_IMPROVEMENT_API_KEY=your-api-key-here
VITE_ANTHROPIC_API_KEY=your-anthropic-key  # Only if calling Claude from frontend
```

## Monitoring & Maintenance

### View Logs

```bash
# Real-time logs
railway logs

# Filter by level
railway logs | grep ERROR
```

### Monitor Health

Setup a monitoring service (UptimeRobot, Pingdom, etc.) to hit:
```
https://your-api.up.railway.app/health
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

### Scaling

Railway auto-scales based on usage. For manual scaling:
1. Dashboard > Project > Settings
2. Adjust "Replicas" slider
3. Set resource limits (CPU, Memory)

### Cost Optimization

- **Hobby Plan**: $5/month + usage (good for MVP)
- **Pro Plan**: $20/month + usage (recommended for production)

Estimate:
- API calls: ~$0.10 per 1000 requests
- Claude API: ~$0.015 per 1000 input tokens
- Storage: Minimal (Supabase handles this)

## Troubleshooting

### Build Fails

**Issue**: Python dependencies fail to install
```bash
# Check requirements.txt format
# Ensure no Windows line endings
dos2unix requirements.txt
```

**Issue**: spaCy model download fails
```bash
# Pre-download in Dockerfile (already included)
RUN python -m spacy download en_core_web_sm
```

### Runtime Errors

**Issue**: "NLP model not loaded"
- Check Docker build logs
- Ensure spaCy download succeeded
- Check memory limits (need ~512MB+)

**Issue**: "Invalid API key"
- Verify environment variables are set
- Check for extra spaces or quotes
- Regenerate API key if needed

**Issue**: Claude API errors
- Verify Anthropic API key
- Check rate limits (default: 1000 RPM)
- Ensure billing is active

### Performance Issues

**Slow response times:**
1. Enable caching for repeated analyses
2. Use Redis for session storage
3. Implement async processing
4. Optimize PDF generation

**High costs:**
1. Implement rate limiting
2. Cache Claude responses
3. Batch similar requests
4. Add usage quotas per user

## Rollback

If deployment fails or has issues:

```bash
# Rollback to previous deployment
railway rollback

# Or specify deployment ID
railway rollback [deployment-id]
```

## CI/CD (Optional)

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]
    paths:
      - 'resume-improvement-api/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      - name: Deploy
        run: |
          cd resume-improvement-api
          railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

## Post-Deployment

### 1. Test All Endpoints

```bash
# Set variables
export API_URL="https://your-api.up.railway.app"
export API_KEY="your-api-key"

# Test analysis
curl -X POST "$API_URL/api/v1/analyze" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://storage.supabase.co/test-resume.pdf",
    "user_id": "test-user",
    "resume_improvement_id": "test-123"
  }'

# Test templates
curl "$API_URL/api/v1/templates"
```

### 2. Update Frontend

Ensure your React app uses the Railway URL:

```typescript
// src/services/resumeImprovement.ts
const API_URL = import.meta.env.VITE_RESUME_IMPROVEMENT_API_URL;
const API_KEY = import.meta.env.VITE_RESUME_IMPROVEMENT_API_KEY;
```

### 3. Monitor First Week

- Watch error rates
- Check response times
- Monitor Claude API usage
- Track conversion rates

### 4. Setup Alerts

Configure alerts for:
- API downtime (> 1 min)
- High error rate (> 5%)
- Slow responses (> 10s)
- High costs (> $50/day)

## Success Criteria

✅ Health check returns 200
✅ All endpoints return valid responses
✅ API key authentication works
✅ Claude AI generates improvements
✅ PDF generation works
✅ Frontend can connect
✅ Logs show no critical errors
✅ Response times < 3s

## Need Help?

- Railway Docs: https://docs.railway.app
- Anthropic Docs: https://docs.anthropic.com
- FastAPI Docs: https://fastapi.tiangolo.com
- WeasyPrint Docs: https://doc.courtbouillon.org/weasyprint/

---

**Ready to deploy? Start with Step 1!**
