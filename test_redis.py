"""
Test Redis Connection and ARQ Job Queue

This script verifies:
1. Redis connection is working
2. ARQ can enqueue jobs
3. Worker configuration is valid

Run this before starting the worker to ensure everything is configured correctly.
"""
import asyncio
import sys
from app.services.queue import get_queue, get_redis_settings, generate_job_id
from app.utils.config import get_settings

async def test_redis_connection():
    """Test basic Redis connectivity"""
    print("=" * 60)
    print("Testing Redis Connection")
    print("=" * 60)

    settings = get_settings()
    print(f"Redis URL: {settings.REDIS_URL}")

    try:
        redis_settings = get_redis_settings()
        print(f"Parsed Redis Settings:")
        print(f"  Host: {redis_settings.host}")
        print(f"  Port: {redis_settings.port}")
        print(f"  Database: {redis_settings.database}")
        print(f"  Password: {'*' * 10 if redis_settings.password else 'None'}")

        queue = get_queue()
        pool = await queue.get_pool()

        print("\n✅ Redis connection successful!")
        print(f"Connection: {pool}")

        await queue.close()
        return True

    except Exception as e:
        print(f"\n❌ Redis connection failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


async def test_job_enqueueing():
    """Test enqueueing a dummy job"""
    print("\n" + "=" * 60)
    print("Testing Job Enqueueing")
    print("=" * 60)

    try:
        queue = get_queue()
        job_id = generate_job_id()

        print(f"Generating test job with ID: {job_id}")

        # Note: This will fail if worker is not running, but it tests the enqueue mechanism
        await queue.enqueue_job(
            "analyze_resume_job",
            job_id=job_id,
            resume_url="https://example.com/test-resume.pdf",
            user_id="test-user"
        )

        print(f"✅ Job enqueued successfully!")
        print(f"Job ID: {job_id}")

        # Try to get job status
        status = await queue.get_job_status(job_id)
        print(f"\nJob Status:")
        print(f"  Status: {status.get('status')}")
        print(f"  Job ID: {status.get('job_id')}")

        await queue.close()
        return True

    except Exception as e:
        print(f"\n❌ Job enqueueing failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


async def test_worker_config():
    """Test worker configuration"""
    print("\n" + "=" * 60)
    print("Testing Worker Configuration")
    print("=" * 60)

    try:
        from app.worker import WorkerSettings

        print(f"Worker Settings:")
        print(f"  Max Jobs: {WorkerSettings.max_jobs}")
        print(f"  Job Timeout: {WorkerSettings.job_timeout}s")
        print(f"  Keep Result: {WorkerSettings.keep_result}s")
        print(f"  Max Retries: {WorkerSettings.max_tries}")

        print(f"\nAvailable Job Functions:")
        for func in WorkerSettings.functions:
            print(f"  - {func.__name__}")

        print("\n✅ Worker configuration is valid!")
        return True

    except Exception as e:
        print(f"\n❌ Worker configuration invalid: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


async def main():
    """Run all tests"""
    print("\n🧪 Redis & ARQ Integration Tests\n")

    results = []

    # Test 1: Redis Connection
    result1 = await test_redis_connection()
    results.append(("Redis Connection", result1))

    # Test 2: Job Enqueueing
    result2 = await test_job_enqueueing()
    results.append(("Job Enqueueing", result2))

    # Test 3: Worker Config
    result3 = await test_worker_config()
    results.append(("Worker Configuration", result3))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start the worker: arq app.worker.WorkerSettings")
        print("3. Start the API: uvicorn app.main:app --reload")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
