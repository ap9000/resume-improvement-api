"""
Job Queue Management for Resume Processing

This module handles enqueueing jobs to the ARQ (asyncio Redis Queue) worker.
Jobs are processed asynchronously by background workers.
"""
import uuid
from typing import Dict, Any, Optional
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from app.utils.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def get_redis_settings() -> RedisSettings:
    """
    Parse REDIS_URL and return RedisSettings for ARQ

    Expected format: redis://[user]:[password]@[host]:[port]
    Railway format: redis://default:password@redis.railway.internal:6379
    """
    redis_url = settings.REDIS_URL

    # Parse the Redis URL
    if redis_url.startswith("redis://"):
        # Remove redis:// prefix
        url_parts = redis_url[8:]

        # Split auth and host
        if "@" in url_parts:
            auth_part, host_part = url_parts.split("@")

            # Parse auth (user:password)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
            else:
                username = None
                password = auth_part

            # Parse host and port
            if ":" in host_part:
                host, port = host_part.rsplit(":", 1)
                port = int(port)
            else:
                host = host_part
                port = 6379
        else:
            # No auth
            username = None
            password = None
            if ":" in url_parts:
                host, port = url_parts.rsplit(":", 1)
                port = int(port)
            else:
                host = url_parts
                port = 6379
    else:
        # Default values
        host = "localhost"
        port = 6379
        username = None
        password = None

    logger.info(f"Redis connection: {host}:{port}")

    return RedisSettings(
        host=host,
        port=port,
        password=password,
        database=0
    )


class JobQueue:
    """
    Manages job enqueueing to Redis/ARQ
    """

    def __init__(self):
        self.redis_pool: Optional[ArqRedis] = None

    async def get_pool(self) -> ArqRedis:
        """
        Get or create Redis connection pool
        """
        if self.redis_pool is None:
            redis_settings = get_redis_settings()
            self.redis_pool = await create_pool(redis_settings)
        return self.redis_pool

    async def enqueue_job(
        self,
        job_function: str,
        job_id: str,
        **kwargs
    ) -> str:
        """
        Enqueue a job to be processed by ARQ worker

        Args:
            job_function: Name of the function to execute (e.g., 'analyze_resume')
            job_id: Unique identifier for this job
            **kwargs: Arguments to pass to the job function

        Returns:
            job_id: The unique identifier for tracking this job
        """
        pool = await self.get_pool()

        try:
            await pool.enqueue_job(
                job_function,
                job_id=job_id,
                **kwargs
            )
            logger.info(f"Enqueued job {job_id} for function {job_function}")
            return job_id

        except Exception as e:
            logger.error(f"Failed to enqueue job {job_id}: {str(e)}")
            raise

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job from Redis

        Returns:
            Dictionary with status information
        """
        pool = await self.get_pool()

        try:
            job_result = await pool.job_result(job_id)

            if job_result is None:
                return {
                    "status": "not_found",
                    "job_id": job_id
                }

            # ARQ job result contains: JobStatus enum
            # JobStatus.deferred, .queued, .in_progress, .complete, .not_found
            return {
                "status": job_result.status.name if hasattr(job_result, 'status') else "unknown",
                "job_id": job_id,
                "result": job_result.result if hasattr(job_result, 'result') else None,
                "enqueue_time": job_result.enqueue_time if hasattr(job_result, 'enqueue_time') else None,
                "start_time": job_result.start_time if hasattr(job_result, 'start_time') else None,
                "finish_time": job_result.finish_time if hasattr(job_result, 'finish_time') else None,
            }

        except Exception as e:
            logger.error(f"Failed to get status for job {job_id}: {str(e)}")
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e)
            }

    async def close(self):
        """
        Close the Redis connection pool
        """
        if self.redis_pool:
            await self.redis_pool.close()
            self.redis_pool = None


# Global queue instance
_queue_instance: Optional[JobQueue] = None


def get_queue() -> JobQueue:
    """
    Get global JobQueue instance (singleton)
    """
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = JobQueue()
    return _queue_instance


async def enqueue_analyze_job(
    job_id: str,
    resume_url: str,
    user_id: Optional[str] = None,
    resume_improvement_id: Optional[str] = None
) -> str:
    """
    Convenience function to enqueue a resume analysis job
    """
    queue = get_queue()
    return await queue.enqueue_job(
        "analyze_resume_job",
        job_id=job_id,
        resume_url=resume_url,
        user_id=user_id,
        resume_improvement_id=resume_improvement_id
    )


async def enqueue_improve_job(
    job_id: str,
    resume_improvement_id: str,
    content: Dict[str, Any],
    focus_areas: Optional[list] = None
) -> str:
    """
    Convenience function to enqueue a resume improvement job
    """
    queue = get_queue()
    return await queue.enqueue_job(
        "improve_resume_job",
        job_id=job_id,
        resume_improvement_id=resume_improvement_id,
        content=content,
        focus_areas=focus_areas or ["bullet_points", "summary", "keywords"]
    )


async def enqueue_generate_job(
    job_id: str,
    resume_improvement_id: str,
    template: str,
    content: Dict[str, Any],
    user_id: str
) -> str:
    """
    Convenience function to enqueue a PDF generation job
    """
    queue = get_queue()
    return await queue.enqueue_job(
        "generate_resume_job",
        job_id=job_id,
        resume_improvement_id=resume_improvement_id,
        template=template,
        content=content,
        user_id=user_id
    )


def generate_job_id() -> str:
    """
    Generate a unique job ID
    """
    return str(uuid.uuid4())
