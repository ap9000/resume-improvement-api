"""
Resume Analysis Router
Handles resume scoring and issue detection
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.services.analyzer import ResumeAnalyzer
from app.utils.auth import verify_api_key
import logging

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(verify_api_key)])
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=AnalyzeResponse)
@limiter.limit("5/minute")  # Expensive operation - limit to 5 per minute
async def analyze_resume(
    request: AnalyzeRequest,
    fastapi_request: Request
) -> AnalyzeResponse:
    """
    Analyze a resume and return scoring + issues

    - **resume_url**: URL to the resume file in storage
    - **user_id**: Optional user ID for tracking
    - **resume_improvement_id**: Optional session ID

    Returns detailed analysis with:
    - Overall and category scores (0-100)
    - List of detected issues with severity
    - Improvement suggestions with priority
    - Resume metadata (word count, sections, etc.)
    """
    try:
        logger.info(f"Analyzing resume: {request.resume_url}")

        # Initialize analyzer with NLP model from app state
        analyzer = ResumeAnalyzer(nlp_model=fastapi_request.app.state.nlp)

        # Perform analysis
        result = await analyzer.analyze(
            resume_url=request.resume_url,
            user_id=request.user_id,
            resume_improvement_id=request.resume_improvement_id
        )

        logger.info(f"Analysis complete. Score: {result.scores.overall_score}")
        return result

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze resume: {str(e)}"
        )


@router.get("/status/{resume_improvement_id}")
async def get_analysis_status(resume_improvement_id: str):
    """
    Get the status of an analysis job
    Useful for async processing in the future
    """
    # TODO: Implement status checking for async jobs
    return {
        "resume_improvement_id": resume_improvement_id,
        "status": "completed",
        "message": "Analysis is complete"
    }
