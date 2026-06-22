"""Tests for the Flask mount, the Django adapter, and the cache adapters (``citry/contrib/``)."""

import pytest

from citry import Citry, Component


class _FakeWsgiHost:
    """Stands in for a Flask app: a ``wsgi_app`` attribute holding the WSGI callable."""

    def __init__(self):
        def wsgi_app(environ, start_response):
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"host:" + environ.get("PATH_INFO", "").encode()]

        self.wsgi_app = wsgi_app


def _wsgi_get(app_callable, path):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(app_callable({"PATH_INFO": path, "REQUEST_METHOD": "GET", "SCRIPT_NAME": ""}, start_response))
    return captured["status"], body


class TestFlaskMount:
    def test_routes_served_under_the_prefix(self):
        from citry.contrib.flask import mount

        c = Citry()
        host = _FakeWsgiHost()
        mount(host, c)
        assert c.mounted_prefix == "/citry"

        status, body = _wsgi_get(host.wsgi_app, "/citry/citry.js")
        assert status == "200 OK"
        assert b"client-side dependency manager" in body

    def test_other_paths_still_reach_the_host(self):
        from citry.contrib.flask import mount

        c = Citry()
        host = _FakeWsgiHost()
        mount(host, c)
        assert _wsgi_get(host.wsgi_app, "/somewhere")[1] == b"host:/somewhere"
        # A prefix-lookalike path is not citry's.
        assert _wsgi_get(host.wsgi_app, "/citryx")[1] == b"host:/citryx"


class TestDjangoAdapter:
    @pytest.fixture(autouse=True)
    def _django(self):
        django = pytest.importorskip("django", reason="the Django adapter tests need django")
        from django.conf import settings

        if not settings.configured:
            settings.configure(ALLOWED_HOSTS=["*"])
            django.setup()
        return django

    def test_urlpatterns_cover_the_route_table(self):
        from citry.contrib.django import urlpatterns

        c = Citry()
        patterns = urlpatterns(c, prefix="/citry")
        assert c.mounted_prefix == "/citry"
        names = [p.name for p in patterns]
        assert "citry_cached_script" in names
        assert "citry_cached_script_vars" in names
        assert "citry_client_runtime" in names
        assert "citry_asset" in names

    def test_view_serves_a_cached_script(self):
        from django.test import RequestFactory

        from citry.contrib.django import urlpatterns

        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"

        patterns = urlpatterns(c)
        by_name = {p.name: p for p in patterns}
        request = RequestFactory().get(f"/citry/cache/{Widget.class_id}.js")
        response = by_name["citry_cached_script"].callback(request, class_id=Widget.class_id, script_type="js")
        assert response.status_code == 200
        assert response.content == b"console.log(1);"
        assert response["Content-Type"].startswith("text/javascript")

        rejected = by_name["citry_cached_script"].callback(
            RequestFactory().post("/x"), class_id=Widget.class_id, script_type="js"
        )
        assert rejected.status_code == 405

    def test_pattern_resolves_dotted_params(self):
        # The cache routes carry two parameters in one path segment, which
        # Django's `path()` syntax cannot express; the adapter falls back to
        # `re_path` there. Resolve through the generated pattern directly.
        from citry.contrib.django import urlpatterns

        c = Citry()
        by_name = {p.name: p for p in urlpatterns(c)}
        match = by_name["citry_cached_script_vars"].resolve("cache/Table_a1b2c3.0ab12c.js")
        assert match is not None
        assert match.kwargs == {"class_id": "Table_a1b2c3", "vars_hash": "0ab12c", "script_type": "js"}
        assert by_name["citry_cached_script_vars"].resolve("cache/Table_a1b2c3.js") is None

    def test_django_cache_adapter(self):
        from django.core.cache.backends.locmem import LocMemCache

        from citry.contrib.django import DjangoCache

        backend = DjangoCache(LocMemCache("citry-test", {}))
        c = Citry(cache=backend)
        assert c.cache is backend
        c.cache.set("k", "v")
        assert c.cache.get("k") == "v"
        assert c.cache.has("k")
        c.cache.delete("k")
        assert c.cache.get("k") is None


class _FakeRedis:
    """The slice of redis-py's API the adapter touches; stores bytes like the real one."""

    def __init__(self):
        self.data = {}
        self.expiries = {}

    def get(self, name):
        return self.data.get(name)

    def set(self, name, value, ex=None):
        self.data[name] = value.encode() if isinstance(value, str) else value
        self.expiries[name] = ex

    def delete(self, name):
        self.data.pop(name, None)

    def exists(self, name):
        return 1 if name in self.data else 0


class _FakeDiskCache:
    """The slice of diskcache.Cache's API the adapter touches."""

    def __init__(self):
        self.data = {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, expire=None):
        self.data[key] = value

    def delete(self, key):
        self.data.pop(key, None)

    def __contains__(self, key):
        return key in self.data


class TestCacheAdapters:
    def test_redis_adapter(self):
        from citry.contrib.caches import RedisCache

        client = _FakeRedis()
        cache = RedisCache(client, prefix="app:")
        cache.set("k", "v")
        assert client.data["app:k"] == b"v"
        assert cache.get("k") == "v"
        assert cache.has("k")
        cache.delete("k")
        assert cache.get("k") is None

    def test_redis_ttl_rounds_up_to_whole_seconds(self):
        from citry.contrib.caches import RedisCache

        client = _FakeRedis()
        RedisCache(client).set("k", "v", ttl=0.2)
        assert client.expiries["k"] == 1
        RedisCache(client).set("k", "v", ttl=None)
        assert client.expiries["k"] is None

    def test_diskcache_adapter_works_as_citry_cache(self):
        from citry.contrib.caches import DiskCache

        c = Citry(cache=DiskCache(_FakeDiskCache()))
        c.cache.set("k", "v")
        assert c.cache.get("k") == "v"
        assert c.cache.has("k")
        c.cache.delete("k")
        assert not c.cache.has("k")
