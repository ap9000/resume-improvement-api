# Quick Setup: Resume Parser Edge Function

## Step 1: Deploy Edge Function to Supabase

### Easiest Method: Dashboard

1. **Open Supabase Dashboard**
   - Go to: https://supabase.com/dashboard/project/gevzqzlncvphkdgeznhj/functions

2. **Create New Function**
   - Click "Deploy a new function"
   - Function name: `parse-resume`
   - Copy entire contents of `supabase/functions/parse-resume/index.ts`
   - Paste into editor
   - Click "Deploy"

3. **Verify Deployment**
   - Function URL: `https://gevzqzlncvphkdgeznhj.supabase.co/functions/v1/parse-resume`
   - Status should show "Deployed"

## Step 2: Get Supabase Anon Key

1. Go to: https://supabase.com/dashboard/project/gevzqzlncvphkdgeznhj/settings/api
2. Copy the **"anon public"** key (NOT service role)
3. Save for next step

## Step 3: Update Railway Environment Variables

### For `resume-improvement-api` service:

1. Go to: https://railway.app → Your Project → `resume-improvement-api`
2. Click "Variables" tab
3. Add these two variables:
   ```
   VITE_RESUME_PARSER_API_URL = https://gevzqzlncvphkdgeznhj.supabase.co/functions/v1
   VITE_RESUME_PARSER_API_KEY = <paste-your-anon-key-here>
   ```
4. Service will automatically redeploy

### For `resume-worker` service:

1. Go to: https://railway.app → Your Project → `resume-worker`
2. Click "Variables" tab
3. Add the **same two variables**:
   ```
   VITE_RESUME_PARSER_API_URL = https://gevzqzlncvphkdgeznhj.supabase.co/functions/v1
   VITE_RESUME_PARSER_API_KEY = <paste-your-anon-key-here>
   ```
4. Service will automatically redeploy

## Step 4: Test Edge Function

Wait ~2 minutes for Railway redeployment, then:

```bash
# Test with your resume
curl -X POST "https://resume-improvement-api-production.up.railway.app/api/v1/analyze/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_url": "https://alekseypelletier.com/AlexPelletier_Resume.pdf",
    "user_id": "alex-test",
    "resume_improvement_id": "edge-function-test"
  }'

# Save the job_id from response
JOB_ID="<paste-job-id-here>"

# Check status after 10 seconds
sleep 10
curl "https://resume-improvement-api-production.up.railway.app/api/v1/analyze/status/$JOB_ID" \
  -H "X-API-Key: YOUR_API_KEY"

# Get result
curl "https://resume-improvement-api-production.up.railway.app/api/v1/analyze/result/$JOB_ID" \
  -H "X-API-Key: YOUR_API_KEY"
```

## Expected Results

### Success Response:
```json
{
  "success": true,
  "job_id": "...",
  "data": {
    "scores": {
      "overall": 85,
      "formatting": 90,
      "content_quality": 80,
      "ats_optimization": 85,
      "skills": 90,
      "professional_summary": 75
    },
    "issues": [...],
    "suggestions": [...],
    "metadata": {
      "word_count": 450,
      "keywords_found": ["..."]
    }
  }
}
```

## Troubleshooting

### Edge Function Returns 404
- Verify function is deployed in Supabase Dashboard
- Check function name is exactly `parse-resume`
- Verify project ref in URL

### Still Getting "Failed to parse resume: 404"
- Check VITE_RESUME_PARSER_API_URL is set in Railway
- Check VITE_RESUME_PARSER_API_KEY is set in Railway
- Verify both API and Worker services have the variables
- Wait for Railway redeployment (~2 minutes)

### Function Deployed But Returns Error
- Check Supabase function logs for detailed error
- Verify PDF URL is publicly accessible
- Test Edge Function directly (see README.md)

## Next Steps After Success

1. ✅ Async queue fully functional end-to-end!
2. ✅ Ready for production use
3. 📝 Optional: Build internal parser for better accuracy (Day 4)
4. 📝 Optional: Add database persistence for job results

---

**Estimated Time:** 10-15 minutes total
