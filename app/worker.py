"""
ARQ Background Worker for Resume Processing

This module defines the background worker that processes async jobs from the Redis queue.
It handles resume analysis, improvement, and PDF generation tasks.

To run the worker:
    arq app.worker.WorkerSettings
"""
import logging
from typing import Dict, Any, Optional
from arq import cron
from arq.connections import RedisSettings
from app.utils.config import get_settings
from app.services.analyzer import ResumeAnalyzer
from app.services.improver import ResumeImprover
from app.services.generator import ResumeGenerator
from app.services.queue import get_redis_settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ============================================================================
# Job Functions (executed by ARQ worker)
# ============================================================================

async def analyze_resume_job(
    ctx: Dict,
    job_id: str,
    resume_url: str,
    user_id: Optional[str] = None,
    resume_improvement_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Background job: Analyze a resume and return scores/suggestions

    Args:
        ctx: ARQ context (provided automatically)
        job_id: Unique job identifier
        resume_url: URL to the resume file
        user_id: Optional user identifier
        resume_improvement_id: Optional resume improvement tracking ID

    Returns:
        Analysis results dictionary
    """
    logger.info(f"[Job {job_id}] Starting resume analysis for {resume_url}")

    try:
        # Initialize analyzer with spaCy model from context
        nlp_model = ctx.get('nlp')
        analyzer = ResumeAnalyzer(nlp_model=nlp_model)

        result = await analyzer.analyze(
            resume_url=resume_url,
            user_id=user_id,
            resume_improvement_id=resume_improvement_id
        )

        logger.info(f"[Job {job_id}] Analysis complete. Overall score: {result.get('scores', {}).get('overall', 0)}")

        return {
            "success": True,
            "job_id": job_id,
            "data": result
        }

    except Exception as e:
        logger.error(f"[Job {job_id}] Analysis failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
            "error_type": type(e).__name__
        }


async def improve_resume_job(
    ctx: Dict,
    job_id: str,
    resume_improvement_id: str,
    content: Dict[str, Any],
    focus_areas: Optional[list] = None
) -> Dict[str, Any]:
    """
    Background job: Generate AI-powered improvements for resume content

    Args:
        ctx: ARQ context (provided automatically)
        job_id: Unique job identifier
        resume_improvement_id: Resume improvement tracking ID
        content: Resume content to improve
        focus_areas: List of areas to focus on (default: all)

    Returns:
        Improvement suggestions dictionary
    """
    logger.info(f"[Job {job_id}] Starting resume improvement for {resume_improvement_id}")

    try:
        improver = ResumeImprover()
        result = await improver.improve(
            resume_improvement_id=resume_improvement_id,
            content=content,
            focus_areas=focus_areas or ["bullet_points", "summary", "keywords"]
        )

        logger.info(f"[Job {job_id}] Improvement complete. Generated {len(result.get('improvements', []))} suggestions")

        return {
            "success": True,
            "job_id": job_id,
            "data": result
        }

    except Exception as e:
        logger.error(f"[Job {job_id}] Improvement failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
            "error_type": type(e).__name__
        }


async def generate_resume_job(
    ctx: Dict,
    job_id: str,
    resume_improvement_id: str,
    template: str,
    content: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Background job: Generate a PDF resume from content

    Args:
        ctx: ARQ context (provided automatically)
        job_id: Unique job identifier
        resume_improvement_id: Resume improvement tracking ID
        template: Template name to use
        content: Resume content to render
        user_id: User identifier for storage path

    Returns:
        Generated PDF information dictionary
    """
    logger.info(f"[Job {job_id}] Starting PDF generation with template '{template}'")

    try:
        generator = ResumeGenerator()
        result = await generator.generate(
            resume_improvement_id=resume_improvement_id,
            template=template,
            content=content,
            user_id=user_id
        )

        logger.info(f"[Job {job_id}] PDF generation complete. File: {result.get('file_name')}")

        return {
            "success": True,
            "job_id": job_id,
            "data": result
        }

    except Exception as e:
        logger.error(f"[Job {job_id}] PDF generation failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
            "error_type": type(e).__name__
        }


# ============================================================================
# Startup/Shutdown Hooks
# ============================================================================

async def startup(ctx: Dict):
    """
    Called when worker starts up
    Initialize any resources needed by worker
    """
    logger.info("🚀 ARQ Worker starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Max concurrent jobs: {settings.ARQ_MAX_JOBS}")
    logger.info(f"Job timeout: {settings.ARQ_JOB_TIMEOUT}s")

    # Load spaCy model for resume analysis
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        ctx['nlp'] = nlp
        logger.info("✅ spaCy model loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load spaCy model: {e}")
        logger.warning("Continuing without spaCy (analysis quality may be reduced)")
        ctx['nlp'] = None


async def shutdown(ctx: Dict):
    """
    Called when worker shuts down
    Clean up any resources
    """
    logger.info("👋 ARQ Worker shutting down...")


# ============================================================================
# Scheduled Jobs (Optional - for future use)
# ============================================================================

async def cleanup_old_jobs(ctx: Dict):
    """
    Scheduled job: Clean up old completed jobs from Redis
    Runs daily at 2 AM
    """
    logger.info("Running scheduled cleanup of old jobs...")
    # TODO: Implement job cleanup logic
    # - Remove jobs older than 30 days
    # - Clean up expired results from Redis
    pass


# ============================================================================
# ARQ Worker Configuration
# ============================================================================

class WorkerSettings:
    """
    ARQ Worker Settings

    This class configures the ARQ worker behavior.
    ARQ will automatically use these settings when starting the worker.
    """

    # Redis connection
    redis_settings = get_redis_settings()

    # Job functions that this worker can execute
    functions = [
        analyze_resume_job,
        improve_resume_job,
        generate_resume_job,
    ]

    # Startup/shutdown hooks
    on_startup = startup
    on_shutdown = shutdown

    # Worker configuration
    max_jobs = settings.ARQ_MAX_JOBS  # Max concurrent jobs
    job_timeout = settings.ARQ_JOB_TIMEOUT  # 5 minutes per job
    keep_result = 3600  # Keep job results for 1 hour

    # Health check configuration
    health_check_interval = 60  # Check every 60 seconds

    # Scheduled jobs (cron-like)
    cron_jobs = [
        # Run cleanup daily at 2 AM
        cron(cleanup_old_jobs, hour=2, minute=0, run_at_startup=False)
    ]

    # Retry configuration
    max_tries = 3  # Retry failed jobs up to 3 times
    retry_delay = 10  # Wait 10 seconds between retries

    # Logging
    log_results = True  # Log job results
    verbose = settings.LOG_LEVEL == "DEBUG"


# ============================================================================
# Development Helper
# ============================================================================

if __name__ == "__main__":
    """
    For development: Print worker configuration
    To run the worker properly, use: arq app.worker.WorkerSettings
    """
    print("=" * 60)
    print("ARQ Worker Configuration")
    print("=" * 60)
    print(f"Redis: {WorkerSettings.redis_settings.host}:{WorkerSettings.redis_settings.port}")
    print(f"Max Jobs: {WorkerSettings.max_jobs}")
    print(f"Job Timeout: {WorkerSettings.job_timeout}s")
    print(f"Keep Results: {WorkerSettings.keep_result}s")
    print(f"Max Retries: {WorkerSettings.max_tries}")
    print("\nAvailable Job Functions:")
    for func in WorkerSettings.functions:
        print(f"  - {func.__name__}")
    print("\nTo start the worker, run:")
    print("  arq app.worker.WorkerSettings")
    print("=" * 60)
