import json
import os
import logging

try:
    import redis
except ImportError:  # AI Suggestion to handle the case where redis is not installed
    redis = None

logger = logging.getLogger(__name__)


# Redis Wrapper class 
class RedisCache:
    def __init__(self, url=None, client=None, default_ttl=300):
        self.default_ttl = default_ttl
        self.client = client if client is not None else self._build_client(url) # AI suggested : self.client = client or self._build_client(url) , if client is invalid, can it be any other value than None ?
        self.enabled = self.client is not None

        if self.enabled and hasattr(self.client, 'ping'):
            try:
                self.client.ping()
            except Exception:
                self.enabled = False

    def _build_client(self, url):
        if redis is None:
            return None
        return redis.Redis.from_url(url or os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)

    def get_json(self, key):
        if not self.enabled or not key:
            return None
        try:
            value = self.client.get(key)
            if value is None:
                return None
            try:     
                return json.loads(value)
            except (json.JSONDecodeError, TypeError) as decode_err:
                logger.error("Corrupted JSON in cache for key '%s': %s", key, decode_err)
                return None
        except Exception as e:
            logger.warning("Redis GET failed for key '%s': %s", key, e)
            return None

    def set_json(self, key, value, ttl=None):
        if not self.enabled or not key:
            return False
        try:
            payload = json.dumps(value, default=str)
            self.client.setex(key, ttl or self.default_ttl, payload)
            return True
        except Exception as e:
            logger.error("Redis SET failed for key '%s': %s", key, e)
            return False

    def delete(self, key):
        if not self.enabled or not key:
            return False
        try:
            result = self.client.delete(key)
            return bool(result)  # Redis returns count, convert to bool
        except Exception as e:
            logger.error("Redis DELETE failed for key '%s': %s", key, e)
            return False
