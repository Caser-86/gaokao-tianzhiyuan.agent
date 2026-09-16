from __future__ import annotations

import threading
from collections import defaultdict, deque
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import UTC, datetime
from time import time
from typing import TypeVar

T = TypeVar("T")


class RequestBudgetError(RuntimeError):
    """Base error for a request rejected by the local budget guard."""


class ModelConcurrencyLimitError(RequestBudgetError):
    pass


class RateLimitExceededError(RequestBudgetError):
    pass


class DailyRequestBudgetExceededError(RequestBudgetError):
    pass


class RequestTimeoutError(RequestBudgetError):
    pass


class RequestBudget:
    """Process-local request guard for a single API worker.

    The guard deliberately uses only the standard library. It provides a safe
    default for one-process deployments and is replaceable by a shared store
    before running multiple API workers.
    """

    def __init__(
        self,
        *,
        max_concurrent: int = 4,
        rate_limit_requests: int = 20,
        rate_limit_window_seconds: int = 60,
        daily_request_budget: int = 1_000,
        clock: Callable[[], float] = time,
    ) -> None:
        self.max_concurrent = max_concurrent
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window_seconds = rate_limit_window_seconds
        self.daily_request_budget = daily_request_budget
        self._clock = clock
        self._lock = threading.Lock()
        self._model_slots = threading.BoundedSemaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(
            max_workers=max_concurrent,
            thread_name_prefix="chat-budget",
        )
        self._rate_events: dict[str, deque[float]] = defaultdict(deque)
        self._daily_date = self._utc_date()
        self._daily_count = 0

    def execute(
        self,
        callback: Callable[[], T],
        *,
        client_ip: str,
        subject: str,
        timeout_seconds: int | float,
    ) -> T:
        self._reserve_request(client_ip=client_ip, subject=subject)
        if not self._model_slots.acquire(blocking=False):
            raise ModelConcurrencyLimitError("model concurrency limit exceeded")

        release_once = threading.Event()

        def run_and_release() -> T:
            try:
                return callback()
            finally:
                if not release_once.is_set():
                    release_once.set()
                    self._model_slots.release()

        try:
            future: Future[T] = self._executor.submit(run_and_release)
        except Exception:
            if not release_once.is_set():
                release_once.set()
                self._model_slots.release()
            raise

        try:
            return future.result(timeout=float(timeout_seconds))
        except FutureTimeoutError as exc:
            raise RequestTimeoutError("chat request timed out") from exc

    def _reserve_request(self, *, client_ip: str, subject: str) -> None:
        now = self._clock()
        rate_key = f"{client_ip.strip() or 'unknown'}|{subject.strip() or 'unknown'}"
        with self._lock:
            current_date = self._utc_date(now)
            if current_date != self._daily_date:
                self._daily_date = current_date
                self._daily_count = 0

            if self._daily_count >= self.daily_request_budget:
                raise DailyRequestBudgetExceededError("daily chat request budget exhausted")

            events = self._rate_events[rate_key]
            cutoff = now - self.rate_limit_window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.rate_limit_requests:
                raise RateLimitExceededError("chat request rate limit exceeded")

            events.append(now)
            self._daily_count += 1

    def _utc_date(self, timestamp: float | None = None):
        value = self._clock() if timestamp is None else timestamp
        return datetime.fromtimestamp(value, tz=UTC).date()
