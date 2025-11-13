# Resume Improvement API

AI-powered resume analysis, scoring, and improvement service for the VA Marketplace.

## Features

- **Resume Analysis**: Score resumes across 5 categories (Formatting, Content, ATS, Skills, Summary)
- **AI Improvements**: Claude-powered content improvements for bullet points, summaries, and keywords
- **PDF Generation**: Generate professional resumes using 4 customizable templates
- **Template Library**: Modern, Professional, ATS-Optimized, and Executive templates

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **AI**: Claude 3.5 Sonnet (Anthropic)
- **PDF Generation**: WeasyPrint + Jinja2
- **NLP**: spaCy + textstat
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Railway

## Project Structure

```
resume-improvement-api/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── routers/
│   │   ├── analyze.py       # Resume analysis endpoints
│   │   ├── improve.py       # AI improvement endpoints
│   │   ├── generate.py      # PDF generation endpoints
│   │   └── templates.py     # Template listing endpoints
│   ├── services/
│   │   ├── analyzer.py      # Resume scoring logic
│   │   ├── improver.py      # Claude AI integration
│   │   └── generator.py     # PDF generation logic
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── utils/
│   │   ├── auth.py          # API key authentication
│   │   └── config.py        # Configuration management
│   └── templates/           # HTML resume templates
│       ├── modern.html
│       ├── professional.html
│       ├── ats-optimized.html
│       └── executive.html
├── requirements.txt
├── Dockerfile
├── railway.json
└── .env.example
```

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
# API Configuration
API_KEY=your-secure-random-api-key
ENVIRONMENT=development

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Claude AI
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional
RATE_LIMIT_PER_MINUTE=10
MAX_FILE_SIZE_MB=5
LOG_LEVEL=INFO
```

### 2. Local Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 3. Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to project
railway link

# Add environment variables
railway variables set API_KEY=your-api-key
railway variables set ANTHROPIC_API_KEY=your-key
railway variables set SUPABASE_URL=your-url
# ... add all other variables

# Deploy
railway up
```

## API Endpoints

### Analysis

**POST /api/v1/analyze**
```json
{
  "resume_url": "https://storage.supabase.co/resumes/user123/resume.pdf",
  "user_id": "user123",
  "resume_improvement_id": "improvement123"
}
```

Returns: Scores, issues, suggestions, and metadata

### Improvement

**POST /api/v1/improve**
```json
{
  "resume_improvement_id": "improvement123",
  "content": { ... },
  "focus_areas": ["bullet_points", "summary", "keywords"]
}
```

Returns: AI-generated improvements with confidence scores

### Generation

**POST /api/v1/generate**
```json
{
  "resume_improvement_id": "improvement123",
  "template": "modern",
  "content": { ... },
  "user_id": "user123"
}
```

Returns: PDF download URL

### Templates

**GET /api/v1/templates**

Returns: List of available templates with descriptions

## Authentication

All endpoints (except `/`, `/health`, `/ready`, `/docs`) require API key authentication.

Add header to all requests:
```
X-API-Key: your-api-key
```

## Scoring System

Total: 100 points across 5 categories:

1. **Formatting (20 pts)**
   - Consistent date formats
   - Clear section headers
   - Proper spacing
   - Optimal length (1-2 pages)

2. **Content Quality (30 pts)**
   - Action verb usage
   - Quantifiable achievements
   - No personal pronouns
   - Strong accomplishments

3. **ATS Optimization (25 pts)**
   - Standard section names
   - No tables/columns
   - Proper formatting
   - Keyword density

4. **Skills Section (15 pts)**
   - Relevant technical skills
   - Software proficiencies
   - Industry keywords

5. **Professional Summary (10 pts)**
   - Clear value proposition
   - Keyword-rich
   - Concise and impactful

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## Monitoring

- Health check: `GET /health`
- Readiness check: `GET /ready`
- Process time in response headers: `X-Process-Time`

## Troubleshooting

### spaCy Model Not Found
```bash
python -m spacy download en_core_web_sm
```

### WeasyPrint Installation Issues
Install system dependencies:
```bash
# macOS
brew install pango

# Ubuntu/Debian
apt-get install libpango-1.0-0 libpangocairo-1.0-0
```

### Claude API Errors
- Check API key is valid
- Verify rate limits
- Check internet connectivity

## Future Enhancements

- [ ] Async processing with job queues
- [ ] Caching for repeated analyses
- [ ] More templates (Creative, Minimalist, etc.)
- [ ] Multi-language support
- [ ] Custom branding options
- [ ] A/B testing for improvements
- [ ] Analytics dashboard

## License

Proprietary - VA Marketplace

## Support

For issues or questions, contact the dev team or open an issue in the main repo.
