"""
Resume Analysis Router
Handles resume scoring and issue detection (Async Job Pattern)
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.services.queue import enqueue_analyze_job, generate_job_id, get_queue
from app.utils.auth import verify_api_key
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_api_key)])
limiter = Limiter(key_func=get_remote_address)


@router.post("/")
@limiter.limit("10/minute")  # Job submission is lightweight
async def analyze_resume(
    request: AnalyzeRequest,
    fastapi_request: Request
) -> Dict[str, Any]:
    """
    Enqueue a resume analysis job (Async Pattern)

    - **resume_url**: URL to the resume file in storage
    - **user_id**: Optional user ID for tracking
    - **resume_improvement_id**: Optional session ID

    Returns immediately with:
    - **job_id**: Unique job identifier for tracking
    - **status**: Initial status (queued)
    - **status_url**: URL to check job status
    - **eta_seconds**: Estimated completion time

    Use the job_id to poll /api/v1/analyze/status/{job_id} for results.
    """
    try:
        # Generate unique job ID
        job_id = generate_job_id()

        logger.info(f"Enqueueing analysis job {job_id} for resume: {request.resume_url}")

        # Enqueue job to ARQ worker
        await enqueue_analyze_job(
            job_id=job_id,
            resume_url=request.resume_url,
            user_id=request.user_id,
            resume_improvement_id=request.resume_improvement_id
        )

        logger.info(f"Job {job_id} enqueued successfully")

        return {
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "status_url": f"/api/v1/analyze/status/{job_id}",
            "result_url": f"/api/v1/analyze/result/{job_id}",
            "eta_seconds": 30,
            "message": "Analysis job queued. Poll status_url for updates."
        }

    except Exception as e:
        logger.error(f"Failed to enqueue analysis job: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue analysis: {str(e)}"
        )


@router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get the status of an analysis job

    Returns:
    - **job_id**: The job identifier
    - **status**: queued | in_progress | complete | failed | not_found
    - **result**: Analysis results (only if status is 'complete')
    - **error**: Error message (only if status is 'failed')
    - **progress**: Job progress information
    """
    try:
        queue = get_queue()
        status_info = await queue.get_job_status(job_id)

        if status_info["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found. It may have expired or never existed."
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
    Get the result of a completed analysis job

    Returns the full AnalyzeResponse once the job is complete.
    If the job is still processing, returns status information instead.
    """
    try:
        queue = get_queue()
        status_info = await queue.get_job_status(job_id)

        if status_info["status"] == "not_found":
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )

        if status_info["status"] == "failed":
            raise HTTPException(
                status_code=500,
                detail=status_info.get("error", "Job failed")
            )

        if status_info["status"] != "complete":
            # Job not done yet, return status
            return {
                "success": False,
                "job_id": job_id,
                "status": status_info["status"],
                "message": "Job not yet complete. Please wait and try again.",
                "status_url": f"/api/v1/analyze/status/{job_id}"
            }

        # Job complete, return result
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
