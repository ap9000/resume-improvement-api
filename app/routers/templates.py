"""
Templates Router
Handles listing and previewing resume templates
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import TemplatesResponse, TemplateInfo, ResumeTemplate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=TemplatesResponse)
async def list_templates() -> TemplatesResponse:
    """
    Get list of all available resume templates

    Returns:
    - Array of template info with descriptions
    - Best use cases for each template
    - Preview/thumbnail URLs
    """
    templates = [
        TemplateInfo(
            id=ResumeTemplate.MODERN,
            name="Modern",
            description="Clean, minimal design with two-column layout. Tech-focused aesthetic.",
            best_for=[
                "Tech-savvy VAs",
                "Digital-first roles",
                "Startup environments",
                "Social media managers"
            ],
            thumbnail_url="/static/templates/modern-thumbnail.png"
        ),
        TemplateInfo(
            id=ResumeTemplate.PROFESSIONAL,
            name="Professional",
            description="Traditional single-column layout. Corporate-friendly and timeless.",
            best_for=[
                "Executive assistants",
                "Corporate environments",
                "Traditional industries",
                "Senior-level positions"
            ],
            thumbnail_url="/static/templates/professional-thumbnail.png"
        ),
        TemplateInfo(
            id=ResumeTemplate.ATS_OPTIMIZED,
            name="ATS-Optimized",
            description="Simple, parser-friendly format. Maximum compatibility with applicant tracking systems.",
            best_for=[
                "Large company applications",
                "Online job portals",
                "Maximum ATS compatibility",
                "Entry to mid-level roles"
            ],
            thumbnail_url="/static/templates/ats-optimized-thumbnail.png"
        ),
        TemplateInfo(
            id=ResumeTemplate.EXECUTIVE,
            name="Executive",
            description="Sophisticated design for senior positions. Emphasizes leadership and achievements.",
            best_for=[
                "Chief of Staff",
                "Executive/Personal assistants",
                "Project managers",
                "Operations managers"
            ],
            thumbnail_url="/static/templates/executive-thumbnail.png"
        )
    ]

    return TemplatesResponse(templates=templates)


@router.get("/{template_id}")
async def get_template_details(template_id: ResumeTemplate):
    """
    Get detailed information about a specific template
    Including full preview and sample
    """
    try:
        # In a real implementation, this would return more details
        template_info = {
            "id": template_id,
            "preview_html": f"/static/templates/{template_id}-preview.html",
            "sample_pdf": f"/static/templates/{template_id}-sample.pdf",
            "features": {
                "ats_friendly": template_id in [ResumeTemplate.ATS_OPTIMIZED, ResumeTemplate.PROFESSIONAL],
                "multi_column": template_id == ResumeTemplate.MODERN,
                "color_scheme": "professional",
                "font_family": "Professional sans-serif"
            }
        }
        return template_info
    except Exception as e:
        logger.error(f"Failed to get template details: {e}")
        raise HTTPException(status_code=404, detail="Template not found")
