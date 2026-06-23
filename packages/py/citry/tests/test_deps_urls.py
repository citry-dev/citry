"""Tests for the routing surface, the mount contract, and the script-serving endpoint logic."""

import pytest

from citry import Citry, Component, Extension
from citry.util.routing import RouteResponse, URLRoute, match_route


class TestRouteMatching:
    def test_param_extraction(self):
        routes = [URLRoute("cache/{class_id}.{script_type}", handler=lambda _request: RouteResponse())]
        matched = match_route(routes, "cache/Table_a1b2c3.js")
        assert matched is not None
        assert matched.params == {"class_id": "Table_a1b2c3", "script_type": "js"}

    def test_first_match_wins(self):
        def vars_handler(_request, **_kwargs):
            return RouteResponse(content="vars")

        def class_handler(_request, **_kwargs):
            return RouteResponse(content="class")

        routes = [
            URLRoute("cache/{class_id}.{vars_hash}.{script_type}", handler=vars_handler),
            URLRoute("cache/{class_id}.{script_type}", handler=class_handler),
        ]
        three = match_route(routes, "cache/Table_a1b2c3.0ab12c.js")
        assert three is not None
        assert three.params["vars_hash"] == "0ab12c"
        two = match_route(routes, "cache/Table_a1b2c3.js")
        assert two is not None
        assert two.route.handler is class_handler

    def test_nested_children_paths_concatenate(self):
        routes = [URLRoute("ext/", children=(URLRoute("probe/status", handler=lambda _request: RouteResponse()),))]
        assert match_route(routes, "ext/probe/status") is not None
        assert match_route(routes, "probe/status") is None

    def test_no_match_returns_none(self):
        assert match_route([URLRoute("a", handler=lambda _request: RouteResponse())], "b") is None

    def test_handler_and_children_are_exclusive(self):
        with pytest.raises(ValueError, match="handler and children"):
            URLRoute("a", handler=lambda _request: RouteResponse(), children=(URLRoute("b"),))


class TestCitryUrls:
    def test_builtin_routes_at_the_root(self):
        c = Citry()
        paths = [route.path for route in c.urls]
        assert "cache/{class_id}.{vars_hash}.{script_type}" in paths
        assert "cache/{class_id}.{script_type}" in paths
        assert "citry.js" in paths

    def test_user_extension_routes_namespaced_under_ext(self):
        class Probe(Extension):
            name = "probe"
            urls = [URLRoute("status", handler=lambda _request: RouteResponse(content="ok"))]

        c = Citry(extensions=[Probe])
        matched = match_route(c.urls, "ext/probe/status")
        assert matched is not None
        assert matched.route.handler(None).content == "ok"

    def test_extensions_get_the_citry_back_reference(self):
        class Probe(Extension):
            name = "probe"

        c = Citry(extensions=[Probe])
        assert c.extensions.get_extension("probe").citry is c


class TestMountContract:
    def test_unmounted_url_building_raises(self):
        c = Citry()
        with pytest.raises(RuntimeError, match="no web integration is mounted"):
            c.build_url("cache/x.js")

    def test_set_mounted_prefix(self):
        c = Citry()
        c.set_mounted_prefix("/citry/")
        assert c.mounted_prefix == "/citry"
        assert c.build_url("citry.js") == "/citry/citry.js"

    def test_prefix_must_be_absolute(self):
        c = Citry()
        with pytest.raises(ValueError, match="start with"):
            c.set_mounted_prefix("citry")


class TestScriptEndpointLogic:
    def _serve(self, c, path, method="GET"):
        """Drive the endpoint through the route table, like an adapter would."""
        matched = match_route(c.urls, path)
        assert matched is not None, path
        assert method in matched.route.methods
        return matched.route.handler(None, **matched.params)

    def test_serves_class_js_and_css(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"
            css = ".w {}"

        str(Widget())  # render once, so the scripts are cached
        js_response = self._serve(c, f"cache/{Widget.class_id}.js")
        assert js_response.status == 200
        assert js_response.content == "console.log(1);"
        assert js_response.content_type == "text/javascript"
        css_response = self._serve(c, f"cache/{Widget.class_id}.css")
        assert css_response.content == ".w {}"
        assert css_response.content_type == "text/css"

    def test_class_script_repopulates_on_cache_miss(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"

        # Nothing rendered, nothing cached: a fresh process serving a request
        # for a class script rebuilds it from the class.
        assert self._serve(c, f"cache/{Widget.class_id}.js").content == "console.log(1);"

    def test_vars_script_served_from_cache(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "$onComponent(() => {});"

            def js_data(self, kwargs, slots=None):
                return {"rows": 3}

        rendered = Widget().render()
        record = next(iter(rendered.context.extra["dependencies"]))
        response = self._serve(c, f"cache/{Widget.class_id}.{record.js_vars_hash}.js")
        assert response.status == 200
        assert "registerComponentData" in response.content

    def test_unknown_class_or_missing_vars_give_404(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log(1);"

        assert self._serve(c, "cache/Nope_000000.js").status == 404
        assert self._serve(c, f"cache/{Widget.class_id}.aaaaaa.js").status == 404
        assert self._serve(c, f"cache/{Widget.class_id}.html").status == 404

    def test_serves_the_runtime(self):
        c = Citry()
        response = self._serve(c, "citry.js")
        assert response.status == 200
        assert "client-side dependency manager" in response.content
        assert response.content_type == "text/javascript"


class TestWsgiApp:
    def _get(self, c, path, method="GET"):
        from citry.contrib.wsgi import wsgi_app

        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        body = b"".join(wsgi_app(c)({"PATH_INFO": path, "REQUEST_METHOD": method}, start_response))
        return captured["status"], captured["headers"], body

    def test_serves_the_runtime(self):
        c = Citry()
        status, headers, body = self._get(c, "/citry.js")
        assert status == "200 OK"
        assert headers["Content-Type"] == "text/javascript"
        assert b"client-side dependency manager" in body

    def test_unknown_404_and_wrong_method_405(self):
        c = Citry()
        assert self._get(c, "/nope")[0] == "404 Not Found"
        assert self._get(c, "/citry.js", method="POST")[0] == "405 Method Not Allowed"
