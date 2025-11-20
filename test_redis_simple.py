"""
Simple Redis Connection Test

Tests Redis connectivity without importing the full app.
"""
import asyncio
import os
from arq import create_pool
from arq.connections import RedisSettings

# Load Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://default:sqjoLRhgsdDHCuVTHcjYLtjATJNUsIyy@redis.railway.internal:6379")


def parse_redis_url(redis_url: str) -> RedisSettings:
    """Parse Redis URL into RedisSettings"""
    if redis_url.startswith("redis://"):
        url_parts = redis_url[8:]  # Remove redis:// prefix

        if "@" in url_parts:
            auth_part, host_part = url_parts.split("@")
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
            else:
                password = auth_part

            if ":" in host_part:
                host, port = host_part.rsplit(":", 1)
                port = int(port)
            else:
                host = host_part
                port = 6379
        else:
            password = None
            if ":" in url_parts:
                host, port = url_parts.rsplit(":", 1)
                port = int(port)
            else:
                host = url_parts
                port = 6379
    else:
        host = "localhost"
        port = 6379
        password = None

    return RedisSettings(
        host=host,
        port=port,
        password=password,
        database=0
    )


async def test_redis():
    """Test Redis connection"""
    print("=" * 60)
    print("Testing Redis Connection")
    print("=" * 60)
    print(f"Redis URL: {REDIS_URL}")

    try:
        redis_settings = parse_redis_url(REDIS_URL)
        print(f"\nParsed Settings:")
        print(f"  Host: {redis_settings.host}")
        print(f"  Port: {redis_settings.port}")
        print(f"  Database: {redis_settings.database}")
        print(f"  Password: {'*' * 10 if redis_settings.password else 'None'}")

        print("\nConnecting to Redis...")
        pool = await create_pool(redis_settings)

        print("✅ Redis connection successful!")

        # Test setting and getting a value
        print("\nTesting Redis operations...")
        await pool.set("test_key", b"test_value")
        value = await pool.get("test_key")
        print(f"  Set and retrieved test value: {value}")

        # Clean up
        await pool.delete("test_key")
        await pool.close()

        print("\n🎉 All Redis tests passed!")
        return 0

    except Exception as e:
        print(f"\n❌ Redis test failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print("\nPossible issues:")
        print("  1. Redis service is not running on Railway")
        print("  2. Network connectivity issues")
        print("  3. Incorrect Redis URL or credentials")
        print(f"  4. Railway Redis might only be accessible from Railway network")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_redis())
    print("\nNote: Railway Redis (redis.railway.internal) is only accessible")
    print("from other Railway services in the same project. For local testing,")
    print("you'll need a local Redis instance or use Railway's public URL if available.")
    exit(exit_code)
