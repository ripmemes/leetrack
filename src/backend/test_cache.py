from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import time
from typing import Any

import pytest

# Ensure backend package can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.cache import RedisCache

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


def can_connect_to_redis(url: str = "redis://localhost:6379/0") -> bool:
    """Check if a real Redis instance is reachable at the given URL."""
    if not HAS_REDIS:
        return False
    try:
        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=1.0)
        return bool(client.ping())
    except Exception:
        return False


class FakeRedis:
    """Mock Redis client for testing that mimics real Redis behavior."""

    def __init__(self, fail_on_operation: str | None = None) -> None:
        self.data: dict[str, Any] = {}
        self.ttls: dict[str, int] = {}
        self.fail_on_operation: str | None = fail_on_operation

    def ping(self) -> bool:
        if self.fail_on_operation == "ping":
            raise Exception("Ping failed")
        return True

    def setex(self, key: str, ttl: int, value: str) -> None:
        if self.fail_on_operation == "set":
            raise Exception("Set failed")
        self.data[key] = value
        self.ttls[key] = ttl

    def get(self, key: str) -> str | None:
        if self.fail_on_operation == "get":
            raise Exception("Get failed")
        return self.data.get(key)

    def delete(self, *keys: str) -> int:
        if self.fail_on_operation == "delete":
            raise Exception("Delete failed")
        count = 0
        for key in keys:
            if key in self.data:
                self.data.pop(key, None)
                self.ttls.pop(key, None)
                count += 1
        return count


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def fake_redis() -> FakeRedis:
    """Fixture providing a fresh FakeRedis mock."""
    return FakeRedis()


@pytest.fixture
def cache(fake_redis: FakeRedis) -> RedisCache:
    """Fixture providing a RedisCache instance backed by FakeRedis."""
    return RedisCache(client=fake_redis)


# ============================================================================
# Test Cases (Pytest function style)
# ============================================================================

def test_set_and_get_roundtrip_preserves_json_data(cache: RedisCache) -> None:
    """Verify that JSON-serializable dictionaries are properly cached and retrieved."""
    assert cache.set_json("demo", {"ok": True}, ttl=30) is True
    assert cache.get_json("demo") == {"ok": True}


def test_getting_nonexistent_key_returns_none(cache: RedisCache) -> None:
    """Verify that querying a non-existent key returns None without error."""
    assert cache.get_json("does_not_exist") is None


def test_deleting_existing_key_removes_it_and_returns_true(cache: RedisCache) -> None:
    """Verify that deleting an existing key removes it and returns True."""
    cache.set_json("key_to_delete", {"data": "value"})
    assert cache.get_json("key_to_delete") is not None

    assert cache.delete("key_to_delete") is True
    assert cache.get_json("key_to_delete") is None


def test_deleting_nonexistent_key_returns_false(cache: RedisCache) -> None:
    """Verify that deleting a non-existent key gracefully returns False."""
    assert cache.delete("does_not_exist") is False


def test_multi_key_delete_removes_all_specified_keys(cache: RedisCache) -> None:
    """Verify that deleting multiple keys in a single call removes all of them."""
    cache.set_json("key1", "val1")
    cache.set_json("key2", "val2")
    cache.set_json("key3", "val3")

    assert cache.delete("key1", "key2") is True
    assert cache.get_json("key1") is None
    assert cache.get_json("key2") is None
    assert cache.get_json("key3") == "val3"


def test_custom_ttl_is_respected(cache: RedisCache, fake_redis: FakeRedis) -> None:
    """Verify that a custom TTL is passed correctly to Redis."""
    cache.set_json("ttl_key", {"data": "value"}, ttl=120)
    assert fake_redis.ttls.get("ttl_key") == 120


def test_default_ttl_is_used_when_none_provided(fake_redis: FakeRedis) -> None:
    """Verify that default_ttl is used when no specific TTL is provided."""
    cache = RedisCache(client=fake_redis, default_ttl=300)
    cache.set_json("default_ttl_key", {"data": "value"})
    assert fake_redis.ttls.get("default_ttl_key") == 300


def test_complex_nested_objects_serialize_and_deserialize(cache: RedisCache) -> None:
    """Verify that complex nested dictionaries and lists are preserved."""
    complex_data = {
        "problems": [
            {"id": 1, "title": "Two Sum", "difficulty": "Easy"},
            {"id": 2, "title": "3Sum", "difficulty": "Medium"},
        ],
        "metadata": {"total": 2, "hasMore": False},
    }
    cache.set_json("problems_list", complex_data)
    retrieved = cache.get_json("problems_list")
    assert retrieved == complex_data


def test_datetime_serialization_converts_to_string_gracefully(cache: RedisCache) -> None:
    """Verify that datetime objects do not cause TypeError during JSON serialization."""
    now = datetime.now()
    data = {"created_at": now, "message": "Test"}

    assert cache.set_json("datetime_key", data) is True
    retrieved = cache.get_json("datetime_key")
    assert retrieved["message"] == "Test"
    assert retrieved["created_at"] is not None


def test_empty_or_none_keys_fail_softly(cache: RedisCache) -> None:
    """Verify that passing empty strings or None for keys returns safe defaults."""
    assert cache.set_json("", {"data": "value"}) is False
    assert cache.get_json("") is None
    assert cache.delete("") is False

    assert cache.set_json(None, {"data": "value"}) is False
    assert cache.get_json(None) is None
    assert cache.delete(None) is False


def test_corrupted_json_returns_none_without_disabling_cache(fake_redis: FakeRedis) -> None:
    """Verify that corrupted JSON payload returns None and does not permanently break cache."""
    cache = RedisCache(client=fake_redis)
    fake_redis.data["corrupt"] = "{invalid json content"

    assert cache.get_json("corrupt") is None
    # Cache must still remain operational for subsequent calls!
    assert cache.enabled is True
    cache.set_json("healthy", {"status": "ok"})
    assert cache.get_json("healthy") == {"status": "ok"}


def test_transient_redis_failure_fails_softly_without_disabling_cache(fake_redis: FakeRedis) -> None:
    """Verify that temporary Redis network blips return None/False without permanently killing cache."""
    fake_redis.fail_on_operation = "get"
    cache = RedisCache(client=fake_redis)

    assert cache.get_json("key") is None
    assert cache.enabled is True

    # Once network recovers, cache operates normally
    fake_redis.fail_on_operation = None
    cache.set_json("key", {"recovered": True})
    assert cache.get_json("key") == {"recovered": True}


def test_cache_invalidation_pattern_cleans_related_keys(cache: RedisCache) -> None:
    """Verify the conversation invalidation flow used across API endpoints."""
    user_id = 42
    conversation_id = 5

    cache.set_json(f"conversations:user:{user_id}", [{"id": conversation_id}])
    cache.set_json(f"conversation:{conversation_id}", {"id": conversation_id})
    cache.set_json(f"messages:conversation:{conversation_id}:user:{user_id}", [])

    # Invalidate using multi-delete
    cache.delete(
        f"conversations:user:{user_id}",
        f"conversation:{conversation_id}",
        f"messages:conversation:{conversation_id}:user:{user_id}",
    )

    assert cache.get_json(f"conversation:{conversation_id}") is None
    assert cache.get_json(f"conversations:user:{user_id}") is None
    assert cache.get_json(f"messages:conversation:{conversation_id}:user:{user_id}") is None


@pytest.fixture
def real_cache() -> Generator[RedisCache, None, None]:
    """Provide a RedisCache connected to real Redis, automatically cleaning up test keys."""
    if not can_connect_to_redis():
        pytest.skip("Real Redis server not available at redis://localhost:6379/0")

    url = os.getenv("REDIS_TEST_URL", "redis://localhost:6379/0")
    cache_instance = RedisCache(url=url)
    yield cache_instance

    # Teardown: Clean up all keys prefixed with 'test:'
    if cache_instance.enabled and cache_instance.client is not None:
        try:
            test_keys = cache_instance.client.keys("test:*")
            if test_keys:
                cache_instance.client.delete(*test_keys)
        except Exception:
            pass


def test_real_redis_set_and_get_roundtrip_succeeds(real_cache: RedisCache) -> None:
    """Verify that JSON values are stored and retrieved from an actual Redis server."""
    key = "test:roundtrip"
    payload = {"status": "ok", "count": 42, "features": ["redis", "cache"]}

    assert real_cache.set_json(key, payload, ttl=30) is True
    assert real_cache.get_json(key) == payload


def test_real_redis_custom_ttl_is_enforced_by_server(real_cache: RedisCache) -> None:
    """Verify that custom TTL is actively set on the Redis server."""
    key = "test:ttl:custom"
    real_cache.set_json(key, {"value": "expires_soon"}, ttl=60)

    server_ttl = real_cache.client.ttl(key)
    assert 0 < server_ttl <= 60


def test_real_redis_key_expires_after_ttl(real_cache: RedisCache) -> None:
    """Verify that a key with short TTL genuinely expires on the Redis server."""
    key = "test:ttl:ephemeral"
    real_cache.set_json(key, {"temp": True}, ttl=1)

    assert real_cache.get_json(key) == {"temp": True}
    time.sleep(1.15)
    assert real_cache.get_json(key) is None


def test_real_redis_default_ttl_is_applied_when_unspecified(real_cache: RedisCache) -> None:
    """Verify that the default TTL is assigned on the Redis server when no TTL is passed."""
    key = "test:ttl:default"
    real_cache.set_json(key, {"value": "uses_default"})

    server_ttl = real_cache.client.ttl(key)
    assert 0 < server_ttl <= real_cache.default_ttl


def test_real_redis_multi_key_delete_removes_all_targeted_keys(real_cache: RedisCache) -> None:
    """Verify that multi-key delete removes multiple keys in a single server command."""
    k1 = "test:multi:1"
    k2 = "test:multi:2"
    k3 = "test:multi:3"

    real_cache.set_json(k1, {"id": 1})
    real_cache.set_json(k2, {"id": 2})
    real_cache.set_json(k3, {"id": 3})

    assert real_cache.delete(k1, k2) is True
    assert real_cache.get_json(k1) is None
    assert real_cache.get_json(k2) is None
    assert real_cache.get_json(k3) == {"id": 3}


def test_real_redis_overwriting_existing_key_updates_data_and_resets_ttl(real_cache: RedisCache) -> None:
    """Verify that setting an existing key overwrites the data and updates server TTL."""
    key = "test:overwrite"
    real_cache.set_json(key, {"version": 1}, ttl=30)
    assert real_cache.get_json(key) == {"version": 1}

    real_cache.set_json(key, {"version": 2}, ttl=120)
    assert real_cache.get_json(key) == {"version": 2}

    server_ttl = real_cache.client.ttl(key)
    assert server_ttl > 60


def test_real_redis_complex_leetcode_payload_roundtrip(real_cache: RedisCache) -> None:
    """Verify storing and retrieving large complex LeetCode responses with unicode and nested dicts."""
    key = "test:leetcode:problems"
    complex_payload = {
        "questions": [
            {
                "questionFrontendId": "1",
                "title": "Two Sum",
                "difficulty": "Easy",
                "tags": ["Array", "Hash Table"],
                "acRate": 54.3,
            },
            {
                "questionFrontendId": "2",
                "title": "Add Two Numbers",
                "difficulty": "Medium",
                "tags": ["Linked List", "Math"],
                "acRate": 42.1,
            },
        ],
        "hasMore": False,
        "total": 2,
    }

    assert real_cache.set_json(key, complex_payload, ttl=60) is True
    retrieved = real_cache.get_json(key)
    assert retrieved == complex_payload


def test_real_redis_datetime_serialization_is_supported(real_cache: RedisCache) -> None:
    """Verify that objects containing datetime are serialized safely to real Redis."""
    key = "test:datetime"
    now = datetime.now(timezone.utc)
    payload = {"timestamp": now, "event": "user_login"}

    assert real_cache.set_json(key, payload, ttl=30) is True
    retrieved = real_cache.get_json(key)
    assert retrieved is not None
    assert retrieved["event"] == "user_login"
    assert "timestamp" in retrieved


def test_real_redis_corrupted_json_in_server_fails_softly(real_cache: RedisCache) -> None:
    """Verify that encountering non-JSON raw strings in Redis returns None and does not disable cache."""
    key = "test:corrupted:raw"
    real_cache.client.set(key, "{this is not valid JSON string")

    assert real_cache.get_json(key) is None
    # Ensure cache is NOT permanently disabled and can continue operating
    assert real_cache.enabled is True

    healthy_key = "test:healthy:after_corrupt"
    assert real_cache.set_json(healthy_key, {"valid": True}) is True
    assert real_cache.get_json(healthy_key) == {"valid": True}


def test_real_redis_conversation_invalidation_workflow(real_cache: RedisCache) -> None:
    """Verify the conversation and message invalidation pattern against real Redis."""
    user_id = 999
    convo_id = 888

    convo_list_key = f"test:conversations:user:{user_id}"
    single_convo_key = f"test:conversation:{convo_id}"
    messages_key = f"test:messages:conversation:{convo_id}:user:{user_id}"

    real_cache.set_json(convo_list_key, [{"id": convo_id, "title": "Dynamic Programming"}], ttl=60)
    real_cache.set_json(single_convo_key, {"id": convo_id, "user_id": user_id}, ttl=60)
    real_cache.set_json(messages_key, [{"role": "user", "content": "How do I solve knapsack?"}], ttl=60)

    # Invalidate all related keys
    assert real_cache.delete(convo_list_key, single_convo_key, messages_key) is True

    assert real_cache.get_json(convo_list_key) is None
    assert real_cache.get_json(single_convo_key) is None
    assert real_cache.get_json(messages_key) is None
