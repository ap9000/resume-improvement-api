"""
Resume Improvement Router
Handles AI-powered content improvements (Async Job Pattern)
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import ImproveRequest, ImproveResponse, ErrorResponse
from app.services.queue import enqueue_improve_job, generate_job_id, get_queue
from app.utils.auth import verify_api_key
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_api_key)])
limiter = Limiter(key_func=get_remote_address)


@router.post("/")
@limiter.limit("10/minute")  # Job submission is lightweight
async def improve_resume(
    improve_request: ImproveRequest,
    request: Request  # slowapi requires this to be named 'request'
) -> Dict[str, Any]:
    """
    Enqueue a resume improvement job (Async Pattern)

    - **resume_improvement_id**: Session ID
    - **content**: Parsed resume content
    - **focus_areas**: Areas to improve (bullet_points, summary, keywords)

    Returns immediately with:
    - **job_id**: Unique job identifier for tracking
    - **status**: Initial status (queued)
    - **status_url**: URL to check job status
    - **eta_seconds**: Estimated completion time

    Use the job_id to poll /api/v1/improve/status/{job_id} for results.
    """
    try:
        # Generate unique job ID
        job_id = generate_job_id()

        logger.info(f"Enqueueing improvement job {job_id} for: {improve_request.resume_improvement_id}")
        logger.info(f"Focus areas: {improve_request.focus_areas}")

        # Enqueue job to ARQ worker
        await enqueue_improve_job(
            job_id=job_id,
            resume_improvement_id=improve_request.resume_improvement_id,
            content=improve_request.content,
            focus_areas=improve_request.focus_areas
        )

        logger.info(f"Job {job_id} enqueued successfully")

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "status_url": f"/api/v1/improve/status/{job_id}",
            "result_url": f"/api/v1/improve/result/{job_id}",
            "eta_seconds": 20,
            "message": "Improvement job queued. Poll status_url for updates."
        }

    except Exception as e:
        logger.error(f"Failed to enqueue improvement job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue improvement: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of an improvement job
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
    Get the result of a completed improvement job
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
                "status_url": f"/api/v1/improve/status/{job_id}"
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


@router.post("/apply")
async def apply_improvements(
    resume_improvement_id: str,
    improvement_ids: list[str]
):
    """
    Apply selected improvements to resume content
    Marks which improvements user chose to use

    TODO: Implement database tracking of which improvements were applied
    """
    try:
        # TODO: Store in database which improvements user selected
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
