"""
Resume Generation Router
Handles PDF generation from templates (Async Job Pattern)
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import GenerateRequest, GenerateResponse, ErrorResponse
from app.services.queue import enqueue_generate_job, generate_job_id, get_queue
from app.utils.auth import verify_api_key
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_api_key)])
limiter = Limiter(key_func=get_remote_address)


@router.post("/")
@limiter.limit("10/minute")  # Job submission is lightweight
async def generate_resume(
    request: GenerateRequest,
    fastapi_request: Request
) -> Dict[str, Any]:
    """
    Enqueue a PDF generation job (Async Pattern)

    - **resume_improvement_id**: Session ID
    - **template**: Template to use (modern, professional, ats-optimized, executive)
    - **content**: Improved resume content
    - **user_id**: User ID for storage path

    Returns immediately with:
    - **job_id**: Unique job identifier for tracking
    - **status**: Initial status (queued)
    - **status_url**: URL to check job status
    - **eta_seconds**: Estimated completion time

    Use the job_id to poll /api/v1/generate/status/{job_id} for the download URL.
    """
    try:
        # Generate unique job ID
        job_id = generate_job_id()

        logger.info(f"Enqueueing PDF generation job {job_id} with template: {request.template}")

        # Enqueue job to ARQ worker
        await enqueue_generate_job(
            job_id=job_id,
            resume_improvement_id=request.resume_improvement_id,
            template=request.template.value,  # Convert enum to string
            content=request.content,
            user_id=request.user_id
        )

        logger.info(f"Job {job_id} enqueued successfully")

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "status_url": f"/api/v1/generate/status/{job_id}",
            "result_url": f"/api/v1/generate/result/{job_id}",
            "eta_seconds": 15,
            "message": "PDF generation job queued. Poll status_url for updates."
        }

    except Exception as e:
        logger.error(f"Failed to enqueue PDF generation job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue PDF generation: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of a PDF generation job
    """
    try:
        queue = get_queue()
        status_info = await queue.get_job_status(job_id)

        if status_info["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        return {
            "success": True,
            "job_id": job_id,
            **status_info
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/result/{job_id}")
async def get_job_result(job_id: str) -> Dict[str, Any]:
    """
    Get the result of a completed PDF generation job

    Returns the download URL and file information once the PDF is generated.
    """
    try:
        queue = get_queue()
        status_info = await queue.get_job_status(job_id)

        if status_info["status"] == "not_found":
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        if status_info["status"] == "failed":
            raise HTTPException(
                status_code=500,
                detail=status_info.get("error", "Job failed")
            )

        if status_info["status"] != "complete":
            return {
                "success": False,
                "job_id": job_id,
                "status": status_info["status"],
                "message": "Job not yet complete. Please wait and try again.",
                "status_url": f"/api/v1/generate/status/{job_id}"
            }

        result = status_info.get("result")
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Job completed but no result found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job result: {str(e)}"
        )


@router.get("/preview/{template}")
async def preview_template(template: str):
    """
    Get a preview/sample of a template
    Returns HTML or thumbnail image
    """
    try:
        from app.services.generator import ResumeGenerator
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
