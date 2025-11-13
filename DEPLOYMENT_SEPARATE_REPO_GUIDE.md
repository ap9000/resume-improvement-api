# Deploying Resume Improvement API to Separate Repo & Railway

Complete guide to move the resume-improvement-api to its own repository and deploy on Railway for integration with the main VA marketplace.

---

## 📋 Prerequisites

- Git installed locally
- Railway CLI installed (`npm install -g @railway/cli`)
- GitHub account
- Railway account (sign up at https://railway.app)
- Supabase project with API keys
- Anthropic API key

---

## Part 1: Create Separate GitHub Repository (15 minutes)

### Step 1: Create New GitHub Repo

1. Go to https://github.com/new
2. **Repository name**: `va-resume-improvement-api`
3. **Description**: "Resume improvement API for VA marketplace - analysis, AI improvements, and PDF generation"
4. **Visibility**: Private (recommended) or Public
5. **DO NOT** initialize with README, .gitignore, or license
6. Click "Create repository"

### Step 2: Prepare Local Directory

```bash
# Navigate to the resume-improvement-api folder
cd /Users/alexpelletier/Documents/vamarketplacenew/resume-improvement-api

# Initialize as a git repository (if not already)
git init

# Create .gitignore if needed
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
test_outputs/
*.log

# Serena
.serena/
EOF
```

### Step 3: Add and Commit Files

```bash
# Add all files
git add .

# Commit with initial message
git commit -m "Initial commit: Resume Improvement API

- FastAPI backend with 5 scoring algorithms
- Claude AI integration for content improvement
- 4 HTML templates for PDF generation (ATS, Professional, Modern, Executive)
- Rate limiting and security (private storage with signed URLs)
- Docker configuration for Railway deployment
- Complete testing and documentation"
```

### Step 4: Push to GitHub

```bash
# Add your GitHub repo as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/va-resume-improvement-api.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**✅ Checkpoint**: Your code is now on GitHub at `github.com/YOUR_USERNAME/va-resume-improvement-api`

---

## Part 2: Deploy to Railway (20 minutes)

### Step 1: Install Railway CLI (if not installed)

```bash
npm install -g @railway/cli

# Login to Railway
railway login
```

### Step 2: Create New Railway Project

```bash
# Navigate to your repo directory
cd /Users/alexpelletier/Documents/vamarketplacenew/resume-improvement-api

# Initialize Railway project
railway init

# When prompted:
# - Choose: "Empty Project"
# - Project name: "va-resume-improvement-api"
```

### Step 3: Link to GitHub Repo

**Option A: Via Railway Dashboard** (Recommended)

1. Go to https://railway.app/dashboard
2. Select your project "va-resume-improvement-api"
3. Click "Settings" → "Connect to GitHub"
4. Select your repository: `YOUR_USERNAME/va-resume-improvement-api`
5. Choose branch: `main`
6. Enable "Deploy on Push" (auto-deploy on git push)

**Option B: Via CLI**

```bash
railway link
# Select your project from the list
```

### Step 4: Set Environment Variables

**Via Railway Dashboard** (Easiest):

1. Go to your project in Railway dashboard
2. Click "Variables" tab
3. Add the following variables:

```env
# API Configuration
API_KEY=<generate-secure-random-key>
ENVIRONMENT=production

# Supabase (from your main VA marketplace project)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-...

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_PER_HOUR=100

# CORS (your frontend URLs)
CORS_ORIGINS=http://localhost:8080,https://your-production-domain.com

# Logging
LOG_LEVEL=INFO
```

**Via Railway CLI**:

```bash
# Set each variable
railway variables set API_KEY="your-secure-random-key"
railway variables set ENVIRONMENT="production"
railway variables set SUPABASE_URL="https://your-project.supabase.co"
railway variables set SUPABASE_ANON_KEY="your-anon-key"
railway variables set SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
railway variables set ANTHROPIC_API_KEY="sk-ant-api03-..."
railway variables set RATE_LIMIT_PER_MINUTE="10"
railway variables set RATE_LIMIT_PER_HOUR="100"
railway variables set CORS_ORIGINS="http://localhost:8080,https://your-domain.com"
railway variables set LOG_LEVEL="INFO"
```

**Generate Secure API Key**:
```bash
# Generate a secure random key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Deploy to Railway

**If using GitHub integration** (auto-deploy):
```bash
# Just push to GitHub and Railway will auto-deploy
git add .
git commit -m "Configure for Railway deployment"
git push origin main
```

**Or deploy directly**:
```bash
railway up
```

### Step 6: Monitor Deployment

```bash
# Watch deployment logs
railway logs

# Or in Railway Dashboard:
# Go to your project → Deployments → View logs
```

**Expected build process**:
1. Docker image builds (5-10 minutes first time)
2. System dependencies installed (gcc, make, libpango)
3. Python dependencies installed
4. spaCy model downloaded (`en_core_web_sm`)
5. NLTK data downloaded
6. Application starts on port 8000
7. Health check passes

### Step 7: Get Your Deployment URL

```bash
# Generate a public domain
railway domain

# Or in Dashboard:
# Settings → Generate Domain
```

**Your API will be available at**:
```
https://va-resume-improvement-api-production.up.railway.app
```

(Railway will generate the exact URL for you)

---

## Part 3: Test the Deployment (10 minutes)

### Test 1: Health Check

```bash
# Save your Railway URL
export API_URL="https://your-deployment.up.railway.app"

# Test health endpoint
curl $API_URL/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": 1234567890,
#   "services": {"nlp": true}
# }
```

### Test 2: API Documentation

Visit in browser:
```
https://your-deployment.up.railway.app/docs
```

You should see the FastAPI Swagger UI with all endpoints.

### Test 3: Templates List (No Auth)

```bash
curl $API_URL/api/v1/templates

# Expected: JSON with 4 template options
```

### Test 4: Resume Analysis (With Auth)

```bash
# Replace with your actual API key from Railway variables
export RESUME_API_KEY="your-api-key-from-railway"

curl -X POST $API_URL/api/v1/analyze \
  -H "X-API-Key: $RESUME_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://your-supabase.co/storage/v1/object/public/profiles/resumes/test.pdf",
    "user_id": "test-user-123",
    "resume_improvement_id": "test-session-123"
  }'

# Should return analysis with scores, issues, suggestions
```

### Test 5: PDF Generation

```bash
curl -X POST $API_URL/api/v1/generate \
  -H "X-API-Key: $RESUME_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_improvement_id": "test-123",
    "template": "modern",
    "content": {
      "name": "Test User",
      "email": "test@example.com",
      "summary": "Test summary",
      "experiences": [],
      "skills": ["Test Skill"]
    },
    "user_id": "test-user-123"
  }'

# Should return:
# {
#   "file_url": "https://...signed-url...",
#   "file_name": "resume_improved_modern_test123.pdf",
#   "file_size": 52345,
#   "generated_at": "2025-01-12T..."
# }
```

**✅ Checkpoint**: All endpoints working? Continue to integration!

---

## Part 4: Integrate with Main VA Marketplace (15 minutes)

### Step 1: Add Environment Variables to Main App

In your main VA marketplace project (React app), add to `.env`:

```env
# Resume Improvement API
VITE_RESUME_IMPROVEMENT_API_URL=https://your-deployment.up.railway.app
VITE_RESUME_IMPROVEMENT_API_KEY=your-secure-api-key
```

### Step 2: Create API Service File

Create `src/services/resumeImprovement.ts` in your main app:

```typescript
import axios from 'axios';

const API_URL = import.meta.env.VITE_RESUME_IMPROVEMENT_API_URL;
const API_KEY = import.meta.env.VITE_RESUME_IMPROVEMENT_API_KEY;

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
});

export interface AnalyzeRequest {
  resume_url: string;
  user_id: string;
  resume_improvement_id: string;
}

export interface AnalyzeResponse {
  success: boolean;
  resume_improvement_id: string;
  scores: {
    overall_score: number;
    formatting_score: number;
    content_quality_score: number;
    ats_optimization_score: number;
    skills_score: number;
    summary_score: number;
  };
  issues: Array<{
    category: string;
    severity: string;
    message: string;
    suggestion: string;
  }>;
  suggestions: string[];
  metadata: {
    total_issues: number;
    critical_issues: number;
    analyzed_at: string;
  };
}

export interface GenerateRequest {
  resume_improvement_id: string;
  template: 'modern' | 'professional' | 'ats-optimized' | 'executive';
  content: any;
  user_id: string;
}

export interface GenerateResponse {
  resume_improvement_id: string;
  template: string;
  file_url: string;
  file_name: string;
  file_size: number;
  generated_at: string;
}

// Get available templates
export const getTemplates = async () => {
  const response = await client.get('/api/v1/templates');
  return response.data;
};

// Analyze resume
export const analyzeResume = async (
  data: AnalyzeRequest
): Promise<AnalyzeResponse> => {
  const response = await client.post('/api/v1/analyze', data);
  return response.data;
};

// Improve content with AI
export const improveContent = async (data: {
  resume_improvement_id: string;
  content: any;
  focus_areas: string[];
}) => {
  const response = await client.post('/api/v1/improve', data);
  return response.data;
};

// Generate PDF
export const generatePDF = async (
  data: GenerateRequest
): Promise<GenerateResponse> => {
  const response = await client.post('/api/v1/generate', data);
  return response.data;
};

export default {
  getTemplates,
  analyzeResume,
  improveContent,
  generatePDF,
};
```

### Step 3: Example Usage in React Component

```typescript
import { useState } from 'react';
import { analyzeResume, generatePDF } from '@/services/resumeImprovement';
import { supabase } from '@/lib/supabase';

export function ResumeImprovementFlow() {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);

  const handleAnalyze = async (resumeFile: File) => {
    setLoading(true);
    try {
      // 1. Upload resume to Supabase storage
      const { data: uploadData, error: uploadError } = await supabase.storage
        .from('profiles')
        .upload(`resumes/${Date.now()}_${resumeFile.name}`, resumeFile);

      if (uploadError) throw uploadError;

      // 2. Get public URL
      const { data: urlData } = supabase.storage
        .from('profiles')
        .getPublicUrl(uploadData.path);

      // 3. Analyze with API
      const result = await analyzeResume({
        resume_url: urlData.publicUrl,
        user_id: 'user-id-here',
        resume_improvement_id: crypto.randomUUID(),
      });

      setAnalysis(result);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (template: string, content: any) => {
    setLoading(true);
    try {
      const result = await generatePDF({
        resume_improvement_id: analysis.resume_improvement_id,
        template: template as any,
        content,
        user_id: 'user-id-here',
      });

      setPdfUrl(result.file_url);

      // Download the PDF
      window.open(result.file_url, '_blank');
    } catch (error) {
      console.error('PDF generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Your UI for upload, analysis display, and PDF generation */}
    </div>
  );
}
```

### Step 4: Update CORS in Railway

Make sure your Railway deployment allows your frontend domain:

```bash
# In Railway dashboard, update CORS_ORIGINS variable to include your frontend URL
CORS_ORIGINS=http://localhost:8080,https://your-production-domain.com
```

---

## Part 5: Production Checklist

### Before Going Live

- [ ] **Environment Variables Set**
  - All Railway variables configured
  - API key is secure and random
  - CORS includes production domain

- [ ] **Supabase Setup**
  - Database migrations run
  - Storage bucket created: `resume-improvements`
  - Storage bucket is private (not public)
  - RLS policies enabled

- [ ] **Testing Complete**
  - Health check returns 200
  - Templates endpoint works
  - Analysis endpoint works with real resume
  - PDF generation works for all 4 templates
  - Rate limiting tested (6th request returns 429)

- [ ] **Integration Tested**
  - Frontend can call all endpoints
  - Error handling works
  - Loading states work
  - PDF downloads correctly

- [ ] **Monitoring Setup**
  - Railway logs accessible
  - Error tracking configured (optional: Sentry)
  - Cost monitoring enabled

### Cost Estimates

**Railway**:
- Free tier: $5 credit/month
- Hobby: $5/month (good for testing)
- Pro: $20/month (recommended for production)

**Estimated usage**:
- 100 analyses/day: ~$0.10/day in compute
- 50 PDF generations/day: ~$0.05/day
- Claude API: ~$0.50/day (for improvements)
- **Total**: ~$20-30/month

**With rate limiting** (configured):
- Max Claude API cost: $2.70/hour → $65/day
- Actual expected: $0.50-2/day with normal usage

---

## Part 6: Ongoing Maintenance

### Deploy Updates

```bash
# Make changes locally
git add .
git commit -m "Update: description of changes"
git push origin main

# Railway will auto-deploy (if GitHub integration enabled)
# Watch deployment: railway logs
```

### View Logs

```bash
# Via CLI
railway logs

# Via Dashboard
# Go to project → Deployments → Click deployment → View logs
```

### Rollback if Needed

```bash
# In Railway Dashboard:
# Deployments → Find previous working deployment → Click "..." → Redeploy
```

### Monitor API Usage

```bash
# Check recent logs for errors
railway logs | grep ERROR

# Monitor health
curl https://your-deployment.up.railway.app/health
```

---

## Troubleshooting

### Issue: Build Fails on Railway

**Error**: "Dockerfile not found" or build fails

**Solution**:
1. Ensure `Dockerfile` is in repo root
2. Check Railway build logs for specific error
3. Verify all files committed: `git status`

### Issue: Health Check Fails

**Error**: Health check returns 503 or times out

**Solution**:
1. Check logs: `railway logs | grep ERROR`
2. Verify spaCy model downloaded: Look for "spaCy model loaded"
3. Check environment variables are set
4. Restart deployment: Railway dashboard → Redeploy

### Issue: CORS Errors in Frontend

**Error**: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solution**:
1. Add frontend URL to `CORS_ORIGINS` in Railway
2. Format: `http://localhost:8080,https://yourdomain.com` (comma-separated, no spaces)
3. Restart deployment

### Issue: PDF Generation Fails

**Error**: "TemplateNotFound" or rendering error

**Solution**:
1. Verify templates exist: `git ls-files app/templates/`
2. Check Docker build logs show templates copied
3. Test locally with Docker: `docker build . && docker run -p 8000:8000`

### Issue: Claude API Errors

**Error**: "API key invalid" or rate limit errors

**Solution**:
1. Verify `ANTHROPIC_API_KEY` in Railway variables
2. Check key is valid at https://console.anthropic.com
3. Verify you have API credits available
4. Check rate limiting isn't too aggressive

### Issue: Storage Upload Fails

**Error**: "Failed to upload to storage" or signed URL error

**Solution**:
1. Verify `SUPABASE_SERVICE_ROLE_KEY` is correct (not anon key)
2. Check storage bucket exists: `resume-improvements`
3. Verify bucket is private
4. Test storage permissions in Supabase dashboard

---

## Summary

**What You've Accomplished**:
1. ✅ Moved resume API to separate GitHub repository
2. ✅ Deployed to Railway with Docker
3. ✅ Configured environment variables and security
4. ✅ Tested all endpoints
5. ✅ Integrated with main VA marketplace app

**Your API is now available at**:
```
https://your-deployment.up.railway.app
```

**Next Steps**:
1. Complete end-to-end testing with real resumes
2. Monitor usage and costs
3. Gather user feedback on templates
4. Add remaining P0 features (input validation, tests, error tracking)

**Support Resources**:
- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- WeasyPrint Docs: https://doc.courtbouillon.org/weasyprint
- This repo's STATUS_REPORT.md for technical details

---

**Estimated Total Time**: 60-90 minutes for complete setup and deployment

🚀 **Your resume improvement API is now live!**
