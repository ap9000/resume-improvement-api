"""
Resume Improvement Router
Handles AI-powered content improvements via Claude
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import ImproveRequest, ImproveResponse, ErrorResponse
from app.services.improver import ResumeImprover
from app.utils.auth import verify_api_key
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_api_key)])
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=ImproveResponse)
@limiter.limit("3/minute")  # Most expensive operation - Claude API calls
async def improve_resume(
    request: ImproveRequest,
    background_tasks: BackgroundTasks,
    fastapi_request: Request
) -> ImproveResponse:
    """
    Get AI-powered improvements for resume content

    - **resume_improvement_id**: Session ID
    - **content**: Parsed resume content
    - **focus_areas**: Areas to improve (bullet_points, summary, keywords)

    Returns:
    - List of specific improvements with original + improved text
    - Reasoning for each improvement
    - Confidence scores
    - Estimated score increase if improvements are applied
    """
    try:
        logger.info(f"Generating improvements for: {request.resume_improvement_id}")
        logger.info(f"Focus areas: {request.focus_areas}")

        # Initialize improver with Claude API
        improver = ResumeImprover()

        # Generate improvements
        result = await improver.improve(
            resume_improvement_id=request.resume_improvement_id,
            content=request.content,
            focus_areas=request.focus_areas
        )

        # Optionally save improvements to database in background
        # background_tasks.add_task(save_improvements_to_db, result)

        logger.info(f"Generated {result.total_improvements} improvements")
        return result

    except Exception as e:
        logger.error(f"Improvement generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate improvements: {str(e)}"
        )


@router.post("/apply")
async def apply_improvements(
    resume_improvement_id: str,
    improvement_ids: list[str]
):
    """
    Apply selected improvements to resume content
    Marks which improvements user chose to use
    """
    try:
        # TODO: Implement applying improvements
        return {
            "success": True,
            "resume_improvement_id": resume_improvement_id,
            "applied_count": len(improvement_ids),
            "message": f"Applied {len(improvement_ids)} improvements"
        }
    except Exception as e:
        logger.error(f"Failed to apply improvements: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_improve(
    requests: list[ImproveRequest]
):
    """
    Batch process multiple improvement requests
    More efficient for multiple sections
    """
    try:
        improver = ResumeImprover()
        results = await improver.batch_improve(requests)
        return {
            "success": True,
            "results": results,
            "total_improvements": sum(r.total_improvements for r in results)
        }
    except Exception as e:
        logger.error(f"Batch improvement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
