# Resume Parser Edge Function

A Supabase Edge Function that parses PDF resumes and returns structured data for the resume analyzer.

## Deployment Instructions

### Option 1: Deploy via Supabase Dashboard (Easiest)

1. Go to https://supabase.com/dashboard/project/gevzqzlncvphkdgeznhj/functions

2. Click "Deploy a new function"

3. Set function name: `parse-resume`

4. Copy/paste the contents of `index.ts` into the editor

5. Click "Deploy function"

6. The function will be available at:
   ```
   https://gevzqzlncvphkdgeznhj.supabase.co/functions/v1/parse-resume
   ```

### Option 2: Deploy via Supabase CLI

```bash
# Install Supabase CLI if you haven't
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref gevzqzlncvphkdgeznhj

# Deploy the function
supabase functions deploy parse-resume

# Optionally set secrets if needed
supabase secrets set SOME_SECRET=value
```

## Configuration After Deployment

### Update Railway Environment Variables

Add these to **both** Railway services (API + Worker):

```bash
VITE_RESUME_PARSER_API_URL=https://gevzqzlncvphkdgeznhj.supabase.co/functions/v1
VITE_RESUME_PARSER_API_KEY=<your-supabase-anon-key>
```

**To get your Supabase anon key:**
1. Go to https://supabase.com/dashboard/project/gevzqzlncvphkdgeznhj/settings/api
2. Copy the "anon public" key
3. Add to Railway environment variables

## Testing the Function

### Test directly via curl:

```bash
curl -X POST \
  https://gevzqzlncvphkdgeznhj.supabase.co/functions/v1/parse-resume \
  -H "Authorization: Bearer YOUR_SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://alekseypelletier.com/AlexPelletier_Resume.pdf",
    "metadata": {
      "user_id": "test",
      "source": "manual_test"
    }
  }'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "name": "Alex Pelletier",
    "email": "alex@example.com",
    "phone": "+1 (555) 123-4567",
    "summary": "...",
    "experiences": [...],
    "education": [...],
    "skills": [...]
  },
  "metadata": {
    "parsed_at": "2025-11-20T...",
    "text_length": 1234
  }
}
```

## How It Works

1. **Download PDF**: Fetches PDF from provided URL
2. **Extract Text**: Uses PDF.js to extract text from all pages
3. **Parse Structure**: Basic regex-based parsing to extract:
   - Contact information (name, email, phone, LinkedIn)
   - Professional summary
   - Work experiences with bullets
   - Education history
   - Skills list
4. **Return JSON**: Structured data matching analyzer expectations

## Limitations (MVP)

- **Basic parsing**: Uses regex patterns, not ML
- **Date parsing**: Returns placeholder dates
- **Section detection**: May miss non-standard section headers
- **Formatting**: Loses PDF formatting (bold, italics, etc.)

## Future Improvements

- Use ML-based resume parser (Day 4)
- Better date extraction (parse "Jan 2021 - Present")
- Company/role separation logic
- Handle multi-column resumes
- Extract certifications and projects

## Troubleshooting

**404 Error**: Function not deployed or wrong URL
- Verify function is deployed in Supabase Dashboard
- Check project ref is correct (gevzqzlncvphkdgeznhj)

**401 Unauthorized**: Wrong API key
- Verify you're using the anon key, not service role key
- Check Authorization header format: `Bearer YOUR_KEY`

**PDF Download Failed**: URL not accessible
- Verify PDF URL is publicly accessible
- Check CORS settings if hosted on restricted domain

**Empty/Bad Results**: Parsing failed
- Check Supabase function logs for errors
- Verify PDF has extractable text (not scanned image)
- Try with different PDF to isolate issue
