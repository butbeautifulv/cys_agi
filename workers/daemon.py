from __future__ import annotations

import asyncio
import signal

from workers.orchestrator import WorkerOrchestrator


class WorkerDaemon:
    """Long-running worker that consumes persona-scoped jobs until stopped or idle."""

    def __init__(
        self,
        persona: str,
        *,
        max_jobs: int | None = None,
        idle_timeout: float = 30.0,
    ) -> None:
        self.persona = persona
        self.max_jobs = max_jobs
        self.idle_timeout = idle_timeout
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    async def run(self) -> int:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self.request_stop)

        orch = WorkerOrchestrator(persona=self.persona)
        processed = 0
        idle_elapsed = 0.0
        poll_interval = 1.0

        while not self._stop:
            if self.max_jobs is not None and processed >= self.max_jobs:
                break
            result = await orch.process_next()
            if result is None:
                idle_elapsed += poll_interval
                if self.idle_timeout > 0 and idle_elapsed >= self.idle_timeout:
                    break
                await asyncio.sleep(poll_interval)
                continue
            processed += 1
            idle_elapsed = 0.0

        return processed


def run_worker_daemon(
    persona: str,
    *,
    max_jobs: int | None = None,
    idle_timeout: float = 30.0,
) -> int:
    return asyncio.run(
        WorkerDaemon(persona, max_jobs=max_jobs, idle_timeout=idle_timeout).run()
    )
