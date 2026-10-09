"""In-process hot-path load probe for the live collaboration manager.

This intentionally avoids Supabase and network latency so it measures the
single-worker receive/revision/fan-out path. Run the browser/network acceptance
test separately in the deployment environment.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import time
from collections import defaultdict

from app.core.auth import CurrentUser
from app.routers.live_collaboration import Connection, LiveCollaborationManager


class ProbeWebSocket:
    def __init__(self, starts: dict[int, float], latencies: list[float]) -> None:
        self.starts = starts
        self.latencies = latencies

    async def send_json(self, message: dict) -> None:
        revision = message.get("revision")
        if isinstance(revision, int) and revision in self.starts:
            self.latencies.append(time.perf_counter() - self.starts[revision])
        await asyncio.sleep(0)


def percentile(values: list[float], percentage: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(len(ordered) * percentage) - 1)
    return ordered[index]


async def run(
    duration: float,
    connections_count: int,
    editors_count: int,
    edits_per_editor_second: int,
) -> None:
    if editors_count > connections_count:
        raise ValueError("editors cannot exceed connections")
    manager = LiveCollaborationManager()
    manager._next_revision[1] = 7_000_000_000
    manager._schedule_live_persist = lambda _live: None
    manager._schedule_canonical = lambda _board, _live: None
    starts: dict[int, float] = {}
    latencies: list[float] = []
    editors: list[Connection] = []
    sequences: defaultdict[str, int] = defaultdict(int)

    connections: set[Connection] = set()
    for index in range(connections_count):
        user_id = f"00000000-0000-0000-0000-{index:012d}"
        user = CurrentUser(
            auth_user_id=user_id,
            profile={"is_active": True},
            role={"code": "leader"},
        )
        connection = Connection(ProbeWebSocket(starts, latencies), user)
        connections.add(connection)
        if len(editors) < editors_count:
            editors.append(connection)
            manager._authorization_cache[(
                user_id,
                "drink-refill",
                "d-rows",
                10,
                "item_name",
                None,
                None,
            )] = (float("inf"), 1, 10)
    manager._connections["drink-refill"] = connections

    edits_per_second = editors_count * edits_per_editor_second
    burst_interval = 1 / edits_per_editor_second
    started_at = time.perf_counter()
    deadline = started_at + duration
    next_burst = started_at
    sent = 0
    while time.perf_counter() < deadline:
        now = time.perf_counter()
        if now < next_burst:
            await asyncio.sleep(next_burst - now)
            continue
        tick = time.perf_counter()
        base_revision = manager._next_revision[1]
        messages = []
        for index, editor in enumerate(editors):
            sequences[editor.user.auth_user_id] += 1
            starts[base_revision + index + 1] = tick
            messages.append(manager.edit("drink-refill", editor, {
                "type": "field_edit",
                "board": "drink-refill",
                "resource": "d-rows",
                "recordId": 10,
                "field": "item_name",
                "value": f"value-{sent + index}",
                "clientId": editor.user.auth_user_id,
                "clientSeq": sequences[editor.user.auth_user_id],
            }))
        await asyncio.gather(*messages)
        sent += len(editors)
        next_burst += burst_interval

    expected_deliveries = sent * connections_count
    delivered = len(latencies)
    p95_ms = percentile(latencies, 0.95) * 1000
    actual_rate = sent / duration
    print(
        f"connections={connections_count} editors={editors_count} sent={sent} "
        f"delivered={delivered}/{expected_deliveries} rate={actual_rate:.1f}/s p95_ms={p95_ms:.2f}"
    )
    if delivered != expected_deliveries:
        raise SystemExit("live collaboration load probe dropped deliveries")
    if p95_ms >= 200:
        raise SystemExit(f"live collaboration load probe exceeded p95 target: {p95_ms:.2f}ms")
    if actual_rate < edits_per_second * 0.95:
        raise SystemExit(f"live collaboration load probe missed input rate: {actual_rate:.1f}/s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=300)
    parser.add_argument("--connections", type=int, default=50)
    parser.add_argument("--editors", type=int, default=20)
    parser.add_argument("--edits-per-editor-second", type=int, default=10)
    args = parser.parse_args()
    asyncio.run(run(
        args.duration,
        args.connections,
        args.editors,
        args.edits_per_editor_second,
    ))
