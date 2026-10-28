"""Bounded execution of pure planning work, outside the ASGI event loop.

One dedicated process keeps the search independent of the event-loop GIL.
One waiting calculation is admitted; further work fails before submission. This
is latency isolation, not parallel CPU throughput. Persistence stays on ASGI.
"""

import asyncio
import copyreg
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass
from decimal import Context, getcontext, localcontext
from functools import partial
from multiprocessing import get_context
from types import MappingProxyType
from typing import Any, ParamSpec, TypeVar

from .domain import PlanningConstraintError

P = ParamSpec("P")
R = TypeVar("R")


def _immutable_mapping(values: dict[Any, Any]) -> MappingProxyType[Any, Any]:
    return MappingProxyType(values)


def _mapping_reduction(
    value: MappingProxyType[Any, Any],
) -> tuple[
    Callable[[dict[Any, Any]], MappingProxyType[Any, Any]], tuple[dict[Any, Any]]
]:
    return _immutable_mapping, (dict(value),)


# Preserve immutable domain mappings through stdlib process serialization;
# do not convert Decimals, enums, identities or calculation outputs to JSON.
copyreg.pickle(MappingProxyType, _mapping_reduction)


class PlanningComputationUnavailableError(Exception):
    """The local bounded planning worker cannot admit another calculation."""


@dataclass(frozen=True)
class _ConstraintFailure:
    code: str
    message: str


def _calculate(context: Context, operation: Callable[[], R]) -> R | _ConstraintFailure:
    # Decimal policy belongs to the caller, never the worker's previous job.
    with localcontext(context):
        try:
            return operation()
        except PlanningConstraintError as error:
            # Its public constructor takes (code, message), while ValueError's
            # standard pickle protocol retains only message. Keep both exactly.
            return _ConstraintFailure(error.code, str(error))


class PlanningComputation:
    def __init__(self) -> None:
        self._pool = ProcessPoolExecutor(max_workers=1, mp_context=get_context("spawn"))
        self._capacity = asyncio.Semaphore(1)
        self._pending = 0
        self._closed = False

    async def run(
        self, operation: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        if self._closed or self._pending >= 2:
            raise PlanningComputationUnavailableError
        self._pending += 1
        try:
            await self._capacity.acquire()
        except BaseException:
            self._pending -= 1
            raise
        if self._closed:
            self._capacity.release()
            self._pending -= 1
            raise PlanningComputationUnavailableError
        loop = asyncio.get_running_loop()
        try:
            future = loop.run_in_executor(
                self._pool,
                _calculate,
                getcontext().copy(),
                partial(operation, *args, **kwargs),
            )
        except BrokenProcessPool as error:
            self._capacity.release()
            self._pending -= 1
            self._closed = True
            raise PlanningComputationUnavailableError from error
        except BaseException:
            self._capacity.release()
            self._pending -= 1
            raise

        def finished(completed: asyncio.Future[R | _ConstraintFailure]) -> None:
            self._pending -= 1
            self._capacity.release()
            # Consume exceptions even if the requesting owner has gone away.
            if not completed.cancelled():
                completed.exception()

        future.add_done_callback(finished)
        # Cancelling an owner must not release capacity while its CPU job is
        # still running. Its late result can never continue to persistence.
        try:
            result = await asyncio.shield(future)
        except BrokenProcessPool as error:
            self._closed = True
            raise PlanningComputationUnavailableError from error
        if isinstance(result, _ConstraintFailure):
            raise PlanningConstraintError(result.code, result.message)
        return result

    async def aclose(self) -> None:
        self._closed = True
        await asyncio.to_thread(self._pool.shutdown, wait=True, cancel_futures=True)
