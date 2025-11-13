# Resume Templates

This directory contains HTML/Jinja2 templates for generating PDF resumes using WeasyPrint.

## Available Templates

### 1. **ATS-Optimized** (`ats-optimized.html`)
- **Design**: Minimal, single-column layout
- **Colors**: Black on white only
- **Font**: Arial (web-safe)
- **Purpose**: Maximum compatibility with Applicant Tracking Systems (ATS)
- **Best For**: Job applications through automated systems, corporate positions

**Features**:
- Clean text hierarchy with no graphics
- Standard section headings (uppercase)
- Simple bullet points
- Inline skills list with bullet separators

### 2. **Professional** (`professional.html`)
- **Design**: Traditional single-column layout
- **Colors**: Navy (#1f2937) accents on white
- **Font**: Georgia (serif) with clean styling
- **Purpose**: Classic, business-appropriate presentation
- **Best For**: Corporate VAs, traditional industries, formal presentations

**Features**:
- Elegant section dividers
- Highlighted professional summary box
- Skill tags with borders
- Traditional date/location formatting

### 3. **Modern** (`modern.html`)
- **Design**: Two-column layout (30% sidebar / 70% main content)
- **Colors**: Teal (#0d9488) accents
- **Font**: Helvetica Neue (sans-serif)
- **Purpose**: Contemporary, eye-catching design
- **Best For**: Tech-savvy VAs, creative positions, modern companies

**Features**:
- Colored header banner with white text
- Skills displayed as colored tags in sidebar
- Education and certifications in sidebar
- Experience and summary in main content area

### 4. **Executive** (`executive.html`)
- **Design**: Sophisticated single-column layout
- **Colors**: Burgundy (#991b1b) accents
- **Font**: Garamond (elegant serif)
- **Purpose**: High-level, polished presentation
- **Best For**: Senior VAs, executive assistants, premium positioning

**Features**:
- Ornate section headers with double underline
- Highlighted executive summary box
- Decorative borders on experience entries
- Premium color palette and spacing

## Data Structure

All templates expect the following data structure (from `app/services/analyzer.py`):

```python
{
    "name": str,                    # Required
    "title": str,                   # Optional - professional title
    "email": str,                   # Optional
    "phone": str,                   # Optional
    "location": str,                # Optional
    "linkedin": str,                # Optional - LinkedIn URL
    "website": str,                 # Optional - Personal website
    "summary": str,                 # Optional - Professional summary
    "experiences": [                # Optional
        {
            "role": str,            # Required
            "company": str,         # Optional
            "location": str,        # Optional
            "start_date": str,      # Optional - Format: "Jan 2021"
            "end_date": str,        # Optional - "Present" or "Dec 2023"
            "responsibilities": [str]  # Optional - List of bullet points
        }
    ],
    "education": [                  # Optional
        {
            "degree": str,          # Required
            "field": str,           # Optional
            "institution": str,     # Optional
            "graduation_date": str, # Optional
            "gpa": str,            # Optional
            "honors": str          # Optional - e.g., "Cum Laude"
        }
    ],
    "skills": [str],               # Optional - List of skills
    "certifications": [            # Optional
        {
            "name": str,           # Required
            "issuer": str,         # Optional
            "date": str            # Optional
        }
    ]
}
```

## Testing Templates Locally

### Setup

```bash
# Navigate to API directory
cd resume-improvement-api

# Create virtual environment (if not exists)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Tests

```bash
# Run test script (from resume-improvement-api directory)
python3 test_templates.py
```

This will:
1. Load sample Virtual Assistant resume data
2. Render all 4 templates
3. Generate test PDFs in `test_outputs/` directory
4. Report success/failure for each template

**Expected Output**:
```
============================================================
Resume Template Testing
============================================================
Output directory: /path/to/test_outputs

Testing template: ats-optimized
  ✓ Template rendered successfully (12,345 characters)
  ✓ PDF generated successfully (45,678 bytes)
  ✓ Saved to: /path/to/test_outputs/ats-optimized_test.pdf

Testing template: professional
  ✓ Template rendered successfully (13,456 characters)
  ✓ PDF generated successfully (52,345 bytes)
  ✓ Saved to: /path/to/test_outputs/professional_test.pdf

Testing template: modern
  ✓ Template rendered successfully (14,567 characters)
  ✓ PDF generated successfully (48,901 bytes)
  ✓ Saved to: /path/to/test_outputs/modern_test.pdf

Testing template: executive
  ✓ Template rendered successfully (15,678 characters)
  ✓ PDF generated successfully (55,234 bytes)
  ✓ Saved to: /path/to/test_outputs/executive_test.pdf

============================================================
Test Results Summary
============================================================
ats-optimized        ✓ PASS
professional         ✓ PASS
modern               ✓ PASS
executive            ✓ PASS

✓ All templates passed!
✓ Test PDFs saved to: /path/to/test_outputs
```

### Manual Testing

You can also test individual templates manually:

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# Setup Jinja2
template_dir = Path("app/templates")
env = Environment(loader=FileSystemLoader(str(template_dir)))

# Sample data
data = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    # ... more fields
}

# Render template
template = env.get_template("modern.html")
html = template.render(content=data)

# Generate PDF
HTML(string=html).write_pdf("output.pdf")
```

## WeasyPrint Compatibility Notes

### ✅ Supported CSS Features
- Basic flexbox (display: flex, justify-content, align-items)
- Grid layout (limited support)
- Border, padding, margin
- Background colors and images
- @page rules for PDF pagination
- Web-safe fonts or embedded fonts
- Basic positioning (relative, absolute)

### ❌ Unsupported CSS Features
- CSS calc() function
- CSS variables (--custom-property)
- Complex transforms
- Animations and transitions
- Some advanced flexbox features
- CSS Grid (advanced features)

### Best Practices
1. **Use @page rules** for controlling PDF page size and margins
2. **Avoid page breaks** inside important content using `page-break-inside: avoid`
3. **Use web-safe fonts** or embed custom fonts
4. **Test thoroughly** - WeasyPrint rendering differs from browsers
5. **Keep CSS simple** - Stick to well-supported properties
6. **Use pt units** for print (11pt = good body text size)

## Integration with Generator Service

The templates are automatically loaded by `app/services/generator.py`:

```python
from app.services.generator import ResumeGenerator
from app.models.schemas import ResumeTemplate

generator = ResumeGenerator()

response = await generator.generate(
    resume_improvement_id="uuid-here",
    template=ResumeTemplate.MODERN,  # or PROFESSIONAL, ATS_OPTIMIZED, EXECUTIVE
    content=resume_data,
    user_id="user-uuid"
)

# Returns GenerateResponse with signed download URL
print(response.file_url)  # Signed URL expires in 1 hour
```

## Troubleshooting

### Template Not Found
**Error**: `jinja2.exceptions.TemplateNotFound: modern.html`

**Solution**: Ensure you're in the correct directory and templates exist:
```bash
ls app/templates/
# Should show: base.html, modern.html, professional.html, ats-optimized.html, executive.html
```

### PDF Rendering Issues
**Error**: Styles not applying correctly in PDF

**Solution**:
- Check CSS is WeasyPrint-compatible (no calc(), CSS vars)
- Verify fonts are web-safe or properly embedded
- Test with simple CSS first, then add complexity

### Missing Data Fields
**Error**: Template renders with blank sections

**Solution**: Ensure your data matches the expected structure. Use optional checks:
```jinja2
{% if content.experiences and content.experiences|length > 0 %}
    <!-- Show experiences -->
{% endif %}
```

## Customization

### Adding New Template

1. Create new template file: `app/templates/new-template.html`
2. Extend base template: `{% extends "base.html" %}`
3. Override `template_styles` block for custom CSS
4. Override `content` block for custom layout
5. Add to `ResumeTemplate` enum in `app/models/schemas.py`
6. Add metadata to templates list in router

### Modifying Existing Template

1. Edit template file directly
2. Test with `test_templates.py`
3. Verify PDF output looks correct
4. Check all data fields render properly

## Files in This Directory

- `base.html` - Base template with shared CSS and structure
- `ats-optimized.html` - ATS-compatible template
- `professional.html` - Traditional professional template
- `modern.html` - Contemporary two-column template
- `executive.html` - Sophisticated executive template
- `README.md` - This file

## Next Steps

After templates are working:
1. ✅ Test all templates locally
2. ✅ Verify PDF output quality
3. Deploy to Railway/production
4. Test end-to-end flow: analyze → improve → generate
5. Get user feedback on template designs
6. Iterate on design based on feedback

## Support

For issues with:
- **Template rendering**: Check Jinja2 syntax and data structure
- **PDF generation**: Review WeasyPrint compatibility notes
- **Styling issues**: Verify CSS is supported by WeasyPrint
- **Missing sections**: Check data structure matches expected format
