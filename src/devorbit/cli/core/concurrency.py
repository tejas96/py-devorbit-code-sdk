"""Concurrency utilities for Devorbit CLI.

This module provides:
- TaskExecutor: Thread pool for parallel operations
- RateLimiter: Rate limiting for API calls
- ResourceLock: Named resource locking

Usage:
    from devorbit.cli.core.concurrency import TaskExecutor, RateLimiter

    executor = TaskExecutor(max_workers=4)
    results = executor.run_parallel([task1, task2, task3])

    limiter = RateLimiter(calls_per_second=10)
    with limiter:
        make_api_call()
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
import contextlib
from contextlib import contextmanager
from dataclasses import dataclass
import threading
import time
from typing import TYPE_CHECKING, Any, TypeVar


if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

T = TypeVar("T")


@dataclass
class TaskResult:
    """Result of a task execution."""

    success: bool
    value: Any = None
    error: Exception | None = None
    execution_time_ms: float = 0.0
    task_id: str = ""

    @classmethod
    def ok(cls, value: Any, execution_time_ms: float = 0.0, task_id: str = "") -> TaskResult:
        """Create a successful result.

        Args:
            value: Result value
            execution_time_ms: Execution time
            task_id: Task identifier

        Returns:
            Successful TaskResult
        """
        return cls(success=True, value=value, execution_time_ms=execution_time_ms, task_id=task_id)

    @classmethod
    def fail(cls, error: Exception, task_id: str = "") -> TaskResult:
        """Create a failed result.

        Args:
            error: Exception that occurred
            task_id: Task identifier

        Returns:
            Failed TaskResult
        """
        return cls(success=False, error=error, task_id=task_id)


class TaskExecutor:
    """Thread pool executor for parallel task execution.

    Provides a simple interface for running tasks in parallel with
    error handling and result collection.
    """

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize task executor.

        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
        self._executor: ThreadPoolExecutor | None = None
        self._lock = threading.Lock()

    def _get_executor(self) -> ThreadPoolExecutor:
        """Get or create the thread pool executor."""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._executor

    def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> Future[T]:
        """Submit a task for execution.

        Args:
            fn: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future representing the pending result
        """
        return self._get_executor().submit(fn, *args, **kwargs)

    def run_parallel(
        self,
        tasks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]],
        timeout: float | None = None,
    ) -> list[TaskResult]:
        """Run multiple tasks in parallel.

        Args:
            tasks: List of (function, args, kwargs) tuples
            timeout: Optional timeout in seconds

        Returns:
            List of TaskResult for each task (in order)
        """
        executor = self._get_executor()
        futures: list[tuple[int, Future[Any]]] = []

        # Submit all tasks
        for i, (fn, args, kwargs) in enumerate(tasks):
            future = executor.submit(fn, *args, **kwargs)
            futures.append((i, future))

        # Collect results in order
        results: list[TaskResult | None] = [None] * len(tasks)

        for i, future in futures:
            start_time = time.perf_counter()
            try:
                value = future.result(timeout=timeout)
                exec_time = (time.perf_counter() - start_time) * 1000
                results[i] = TaskResult.ok(value, execution_time_ms=exec_time, task_id=str(i))
            except Exception as e:
                results[i] = TaskResult.fail(e, task_id=str(i))

        return [r for r in results if r is not None]

    def map(
        self,
        fn: Callable[[T], Any],
        items: list[T],
        timeout: float | None = None,
    ) -> list[TaskResult]:
        """Map a function over items in parallel.

        Args:
            fn: Function to apply
            items: Items to process
            timeout: Optional timeout

        Returns:
            List of TaskResult for each item
        """
        tasks: list[tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]]] = [
            (fn, (item,), {}) for item in items
        ]
        return self.run_parallel(tasks, timeout=timeout)

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor.

        Args:
            wait: Wait for pending tasks to complete
        """
        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None


class RateLimiter:
    """Token bucket rate limiter.

    Limits the rate of operations to prevent API throttling.
    """

    def __init__(
        self,
        calls_per_second: float = 10.0,
        burst_size: int | None = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            calls_per_second: Maximum sustained rate
            burst_size: Maximum burst size (defaults to 2x rate)
        """
        self.rate = calls_per_second
        self.burst_size = burst_size or int(calls_per_second * 2)
        self._tokens = float(self.burst_size)
        self._last_update = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.burst_size, self._tokens + elapsed * self.rate)
        self._last_update = now

    def acquire(self, tokens: int = 1, blocking: bool = True) -> bool:
        """Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire
            blocking: Wait for tokens if not available

        Returns:
            True if tokens were acquired
        """
        with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            if not blocking:
                return False

            # Calculate wait time
            deficit = tokens - self._tokens
            wait_time = deficit / self.rate

        # Wait outside lock
        time.sleep(wait_time)

        # Retry acquisition
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @contextmanager
    def limit(self, tokens: int = 1) -> Iterator[None]:
        """Context manager for rate-limited operations.

        Args:
            tokens: Number of tokens to acquire

        Yields:
            None after acquiring tokens
        """
        self.acquire(tokens)
        yield

    def __enter__(self) -> RateLimiter:
        """Enter context manager."""
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        pass


class ResourceLock:
    """Named resource locking for preventing concurrent access.

    Provides fine-grained locking for specific resources (e.g., files).
    """

    def __init__(self) -> None:
        """Initialize resource lock manager."""
        self._locks: dict[str, threading.RLock] = {}
        self._master_lock = threading.Lock()

    def _get_lock(self, resource: str) -> threading.RLock:
        """Get or create lock for a resource.

        Args:
            resource: Resource identifier

        Returns:
            Lock for the resource
        """
        if resource not in self._locks:
            with self._master_lock:
                if resource not in self._locks:
                    self._locks[resource] = threading.RLock()
        return self._locks[resource]

    def acquire(self, resource: str, blocking: bool = True, timeout: float = -1) -> bool:
        """Acquire lock on a resource.

        Args:
            resource: Resource identifier
            blocking: Wait for lock
            timeout: Timeout in seconds (-1 for infinite)

        Returns:
            True if lock acquired
        """
        lock = self._get_lock(resource)
        return lock.acquire(blocking=blocking, timeout=timeout)

    def release(self, resource: str) -> None:
        """Release lock on a resource.

        Args:
            resource: Resource identifier
        """
        if resource in self._locks:
            with contextlib.suppress(RuntimeError):
                self._locks[resource].release()

    @contextmanager
    def lock(self, resource: str, timeout: float = -1) -> Iterator[bool]:
        """Context manager for resource locking.

        Args:
            resource: Resource identifier
            timeout: Timeout in seconds

        Yields:
            True if lock was acquired
        """
        acquired = self.acquire(resource, timeout=timeout)
        try:
            yield acquired
        finally:
            if acquired:
                self.release(resource)

    def is_locked(self, resource: str) -> bool:
        """Check if a resource is locked.

        Args:
            resource: Resource identifier

        Returns:
            True if locked
        """
        if resource not in self._locks:
            return False

        lock = self._locks[resource]
        acquired = lock.acquire(blocking=False)
        if acquired:
            lock.release()
            return False
        return True

    def cleanup(self) -> None:
        """Remove unused locks."""
        with self._master_lock:
            to_remove = []
            for resource, lock in self._locks.items():
                acquired = lock.acquire(blocking=False)
                if acquired:
                    lock.release()
                    to_remove.append(resource)

            for resource in to_remove:
                del self._locks[resource]


# Singleton holders
class _TaskExecutorHolder:
    """Holder for global TaskExecutor instance."""

    instance: TaskExecutor | None = None


class _ResourceLockHolder:
    """Holder for global ResourceLock instance."""

    instance: ResourceLock | None = None


def get_task_executor(max_workers: int = 4) -> TaskExecutor:
    """Get the global task executor.

    Args:
        max_workers: Maximum workers (only used on first call)

    Returns:
        Global TaskExecutor instance
    """
    if _TaskExecutorHolder.instance is None:
        _TaskExecutorHolder.instance = TaskExecutor(max_workers=max_workers)
    return _TaskExecutorHolder.instance


def get_resource_lock() -> ResourceLock:
    """Get the global resource lock manager.

    Returns:
        Global ResourceLock instance
    """
    if _ResourceLockHolder.instance is None:
        _ResourceLockHolder.instance = ResourceLock()
    return _ResourceLockHolder.instance


__all__ = [
    "RateLimiter",
    "ResourceLock",
    "TaskExecutor",
    "TaskResult",
    "get_resource_lock",
    "get_task_executor",
]
