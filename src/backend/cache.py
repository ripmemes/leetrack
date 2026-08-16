import json
import os

try:
    import redis
except ImportError:  # AI Suggestion to handle the case where redis is not installed
    redis = None


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
            return json.loads(value)
        except Exception:
            self.enabled = False
            return None

    def set_json(self, key, value, ttl=None):
        if not self.enabled or not key:
            return False
        try:
            payload = json.dumps(value, default=str)
            self.client.setex(key, ttl or self.default_ttl, payload)
            return True
        except Exception:
            self.enabled = False
            return False

    def delete(self, key):
        if not self.enabled or not key:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception:
            self.enabled = False
            return False
