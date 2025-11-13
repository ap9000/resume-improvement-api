"""
Resume Generation Router
Handles PDF generation from templates
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import GenerateRequest, GenerateResponse, ErrorResponse
from app.services.generator import ResumeGenerator
from app.utils.auth import verify_api_key
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_api_key)])
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=GenerateResponse)
@limiter.limit("10/minute")  # PDF generation is CPU intensive
async def generate_resume(
    request: GenerateRequest,
    fastapi_request: Request
) -> GenerateResponse:
    """
    Generate an improved resume PDF from template

    - **resume_improvement_id**: Session ID
    - **template**: Template to use (modern, professional, ats-optimized, executive)
    - **content**: Improved resume content
    - **user_id**: User ID for storage path

    Returns:
    - URL to download the generated PDF
    - File name and size
    - Generation timestamp
    """
    try:
        logger.info(f"Generating resume with template: {request.template}")

        # Initialize generator
        generator = ResumeGenerator()

        # Generate PDF
        result = await generator.generate(
            resume_improvement_id=request.resume_improvement_id,
            template=request.template,
            content=request.content,
            user_id=request.user_id
        )

        logger.info(f"Generated PDF: {result.file_name} ({result.file_size} bytes)")
        return result

    except Exception as e:
        logger.error(f"PDF generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.get("/preview/{template}")
async def preview_template(template: str):
    """
    Get a preview/sample of a template
    Returns HTML or thumbnail image
    """
    try:
        generator = ResumeGenerator()
        preview = await generator.get_template_preview(template)
        return {
            "template": template,
            "preview_url": preview
        }
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regenerate")
async def regenerate_resume(
    resume_improvement_id: str,
    template: str,
    user_id: str
):
    """
    Regenerate a resume with a different template
    Reuses existing improved content
    """
    try:
        generator = ResumeGenerator()

        # TODO: Fetch improved content from database
        # content = await get_improved_content(resume_improvement_id)

        result = await generator.generate(
            resume_improvement_id=resume_improvement_id,
            template=template,
            content={},  # Fetch from DB
            user_id=user_id
        )

        return result
    except Exception as e:
        logger.error(f"Regeneration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
