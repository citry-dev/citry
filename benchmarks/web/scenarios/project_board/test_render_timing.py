"""Check render attribution across nested calls and worker contexts."""

import asyncio
import unittest
from unittest.mock import patch

import pytest
from render_timing import (
    PreparationTimings,
    RenderTimingMiddleware,
    current,
    discard_pending_preparation,
    pending_preparation,
    preparation_scope,
    preparation_span,
    render_span,
    take_pending_preparation,
)


class PreparationTimingTests(unittest.IsolatedAsyncioTestCase):
    async def test_disjoint_spans_sum_and_nested_work_counts_once(self):
        timing = PreparationTimings()
        with patch("render_timing.perf_counter", side_effect=[1.0, 1.002, 3.0, 3.004]):
            with preparation_scope(timing):
                with preparation_span(), preparation_span():
                    pass
                with preparation_span():
                    pass
        assert timing.duration == pytest.approx(0.006)
        assert timing.count == 2

    async def test_pending_accumulators_are_task_local_and_consumed_once(self):
        arrived = 0
        together = asyncio.Event()

        async def task() -> PreparationTimings:
            nonlocal arrived
            timing = pending_preparation()
            arrived += 1
            if arrived == 2:
                together.set()
            await together.wait()
            assert take_pending_preparation() is timing
            assert take_pending_preparation() is None
            return timing

        first, second = await asyncio.gather(task(), task())
        assert first is not second
        discard_pending_preparation()


class RenderTimingTests(unittest.IsolatedAsyncioTestCase):
    async def response(self, render=True, status=200):
        messages = []

        def work():
            if render:
                with render_span(), render_span():
                    pass

        async def app(scope, receive, send):
            await asyncio.to_thread(work)
            await send(
                {
                    "type": "http.response.start",
                    "status": status,
                    "headers": [(b"server-timing", b"application;dur=20")],
                }
            )

        async def send(message):
            messages.append(message)

        with patch("render_timing.perf_counter", side_effect=[1.0, 1.005]):
            await RenderTimingMiddleware(app)({"type": "http"}, None, send)
        assert current.get() is None
        return dict(messages[0]["headers"])[b"server-timing"]

    async def test_nested_worker_render_counted_once(self):
        assert await self.response() == b"application;dur=20, render;dur=5.000"

    async def test_non_render_response_has_no_metric(self):
        assert await self.response(render=False) == b"application;dur=20"

    async def test_failed_response_has_no_metric(self):
        assert await self.response(status=500) == b"application;dur=20"

    async def test_simultaneous_requests_keep_distinct_accumulators(self):
        arrived = 0
        together = asyncio.Event()
        accumulators = []
        results = {}

        async def app(scope, receive, send):
            nonlocal arrived
            accumulators.append(current.get())
            arrived += 1
            if arrived == 2:
                together.set()
            await together.wait()
            for _ in range(scope["calls"]):
                await asyncio.to_thread(lambda: self.worker_span())
            await send({"type": "http.response.start", "status": 200, "headers": []})

        async def request(calls):
            async def send(message):
                results[calls] = dict(message["headers"])[b"server-timing"]

            await RenderTimingMiddleware(app)({"type": "http", "calls": calls}, None, send)

        await asyncio.gather(request(1), request(2))
        assert accumulators[0] is not accumulators[1]
        assert sorted(item.count for item in accumulators) == [1, 2]
        assert set(results) == {1, 2}
        assert current.get() is None

    @staticmethod
    def worker_span():
        with render_span():
            pass

    async def test_rejects_parallel_worker_span_in_same_request(self):
        async def app(scope, receive, send):
            with render_span():
                with pytest.raises(RuntimeError, match="Concurrent render threads"):
                    await asyncio.to_thread(self.worker_span)

        await RenderTimingMiddleware(app)({"type": "http"}, None, None)
        assert current.get() is None
