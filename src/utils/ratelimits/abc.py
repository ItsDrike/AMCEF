import itertools
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from functools import wraps
from time import time
from typing import Generic, ParamSpec, TypeVar, cast

from aioredis import Redis
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response

P = ParamSpec("P")
T = TypeVar("T")
log = logging.getLogger(__name__)


class OnCooldownError(Exception):
    """An exception class to provide information on the current cooldown."""

    def __init__(self, remaining: int, *args: object) -> None:
        super().__init__(*args)
        self.remaining = remaining


class BucketBase(ABC, Generic[T]):
    """The base class for all rate limit buckets."""

    _bucket_counter = itertools.count(0)

    def __init__(
        self,
        *,
        requests: int,
        time_period: float,
        cooldown: float,
    ):
        """
        Bucket constructor. Limits are enforced as `requests` per `time_period`.

        :param requests: The maximum allowed requests for this bucket per `time_unit`.
        :param time_period: The time period for requests in seconds.
        :param cooldown: The penalty cooldown in seconds for surpassing the allowed request limit.
        """
        self.requests = requests
        self.time_period = time_period
        self.cooldown = cooldown

        # Assign each instance a different bucket number so that we can distinguish
        # between the bucket instances when storing/accessing data into/from a database.
        self.bucket_no = next(self._bucket_counter)

    async def handle_request(self, bucket_key: T) -> None:
        """Logic occcuring on a new call to bucket rate limited route."""
        log.debug(f"Handling rate-limited route for bucket key {bucket_key} (bucket #{self.bucket_no})")
        cooldown_remaining = await self.get_cooldown(bucket_key)
        if cooldown_remaining > 0:
            log.debug(
                f"Request attempt for bucket key {bucket_key}, which is currently under cooldown, made."
                f" Interaction prevented, {cooldown_remaining} seconds of cooldown remaining (bucket #{self.bucket_no})"
            )
            raise OnCooldownError(cooldown_remaining)

        remaining_requests = await self.get_remaining_requests(bucket_key)
        if remaining_requests <= 0:
            log.debug(
                f"Request attempt for bucket key {bucket_key} with {remaining_requests} remaining requests made."
                f" Interaction NOT within ratelimit, trigering cooldown (bucket #{self.bucket_no})"
            )
            # Attempted to make another request, with no remaining requests, trigger the penalty cooldown
            await self.start_cooldown(bucket_key)
            cooldown_remaining = await self.get_cooldown(bucket_key)
            raise OnCooldownError(cooldown_remaining)

        log.debug(
            f"Request attempt for bucket key {bucket_key} with {remaining_requests} remaining requests made."
            f" Interaction is within ratelimit, recording the attempt (bucket #{self.bucket_no})"
        )
        await self.record_interaction(bucket_key)

    def __call__(self, func: Callable[P, Awaitable[Response]]) -> Callable[P, Awaitable[Response]]:
        """Decorate route function returning a custom caller enforcing bucket rate limits."""

        @wraps(func)
        async def caller(*args: P.args, **kwargs: P.kwargs) -> Response:
            if "request" not in kwargs:
                raise AttributeError("Bucket limiting requires the route function to have a 'request' attribute.")

            request = cast(Request, kwargs["request"])
            await self.pre_call(request)
            bucket_key = await self.get_bucket_key(request)

            try:
                await self.handle_request(bucket_key)
            except OnCooldownError as exc:
                response = JSONResponse({"message": "You're currently on cooldown. Try again later."}, 429)
                await self.add_cooldown_headers(response, exc.remaining)
            else:
                response = await func(*args, **kwargs)
                await self.add_headers(response, bucket_key)
            return response

        return caller

    async def add_headers(self, response: Response, bucket_key: T) -> None:
        """Add ratelimit informing headers to provided response."""
        remaining_interactions = await self.get_remaining_requests(bucket_key)
        time_until_reset = await self.get_reset_time(bucket_key)

        response.headers.append("Requests-Limit", str(self.requests))
        response.headers.append("Requests-Period", str(self.time_period))
        response.headers.append("Requests-Reminding", str(remaining_interactions))
        response.headers.append("Requests-Reset", str(time_until_reset))

    async def add_cooldown_headers(self, response: Response, remaining_seconds: int) -> None:
        """
        Add cooldown informing headers to provided response.

        This function is called instead of add_headers when we're under cooldown, as we usually
        don't want to include the regular headers along with the cooldown one, instead we just
        want the cooldown header(s). This can however be overridden to call add_headers along
        with this original implementation if having regular headers too is desired.
        """
        response.headers.append("Cooldown-Reset", str(remaining_seconds))

    async def pre_call(self, request: Request) -> None:
        """A hook function called before handling each request to a rate-limited route."""
        log.debug(f"Someone accessed rate-limited route (pre-call) (bucket #{self.bucket_no})")

    @abstractmethod
    async def get_bucket_key(self, request: Request) -> T:
        """
        Given a request, parse it and obtain id/key of the specific bucket it belongs to.

        This depends on the specific bucket implementation, as it needs to handle producing a bucket
        key/id that identifies the bucket this request belongs under. Generally, this will likely be the
        primary key for a database of all buckets. (For example for a user based bucket, this key could
        be the user id.)
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_remaining_requests(self, bucket_key: T) -> int:
        """
        Obtain the amount of remaining requests for given bucket.

        This should also check for the remaining reset time, which if gets to 0 should perform the reset,
        setting the amount of remaining requests back to maximum (self.requests).
        """
        raise NotImplementedError()

    @abstractmethod
    async def record_interaction(self, bucket_key: T) -> None:
        """
        Log a new interaction (a new request on rate-limited route) belonging to given bucket.

        This should decrease the amount of remaining requests with each call.
        """
        raise NotImplementedError()

    @abstractmethod
    async def get_cooldown(self, bucket_key: T) -> int:
        """
        Return the time, in seconds, until cooldown for this bucket ends, or 0 if cooldown isn't active.

        This should also perform cleanup if the triggered cooldown is no longer active (the time period has passed),
        marking this cooldown as inactive/stopped until another start_cooldown.
        """
        raise NotImplementedError()

    @abstractmethod
    async def start_cooldown(self, bucket_key: T) -> None:
        """Trigger cooldown on given bucket for self.cooldown time."""
        raise NotImplementedError()

    @abstractmethod
    async def get_reset_time(self, bucket_key: T) -> int:
        """Get the time until available interactions are reset back to the original amount for given bucket."""
        raise NotImplementedError()


class RedisBucketBase(BucketBase[T]):
    """The base class for all rate-limit buckets backed by Redis."""

    redis: Redis = None  # type: ignore # This will always get set in pre_call

    def get_redis_key(self, bucket_key: T, name: str) -> str:
        """Get a redis key unique to this bucket and bucket_key for given name."""
        return f"bucket-{self.bucket_no}-{bucket_key}-{name}"

    async def pre_call(self, request: Request) -> None:
        """Get redis pool from the request state data before handling a request to rate-limited route."""
        await super().pre_call(request)
        if self.redis is None:
            self.redis = request.state.redis_pool

    async def get_remaining_requests(self, bucket_key: T) -> int:
        redis_key = self.get_redis_key(bucket_key, "interaction")

        # Cleanup expired entries
        await self.redis.zremrangebyscore(redis_key, max=time(), min=0)

        # Get still active entries and subtract them from total allowed requests, getting the reminding requests
        interactions = int(await self.redis.zcard(redis_key) or 0)
        return self.requests - interactions

    async def record_interaction(self, bucket_key: T) -> None:
        redis_key = self.get_redis_key(bucket_key, "interaction")

        # We use UUIDs here as something random and unique for each interaction
        await self.redis.zadd(redis_key, {str(uuid.uuid4()): time() + self.time_period})

    async def start_cooldown(self, bucket_key: T) -> None:
        redis_key = self.get_redis_key(bucket_key, "cooldown")

        await self.redis.set(redis_key, 1)
        await self.redis.expireat(redis_key, int(time() + self.cooldown))

    async def get_cooldown(self, bucket_key: T) -> int:
        redis_key = self.get_redis_key(bucket_key, "cooldown")

        if not await self.redis.get(redis_key):
            return 0

        return await self.redis.ttl(redis_key)

    async def get_reset_time(self, bucket_key: T) -> int:
        redis_key = self.get_redis_key(bucket_key, "interaction")

        # Get the entry (uuid) with highest score (reset time), since score represents time
        # this will be the interaction entry which will take longest to get reset
        newest_uuid = await self.redis.zrange(redis_key, 0, 0, desc=True, withscores=True)

        if not newest_uuid:
            return 0

        # Scores use absolute time stamps, subtract current time to get seconds reminding
        rem_seconds = int(newest_uuid[0][1] - time())

        # Make sure we don't return a negative number, it's possible that this interaction has
        # already reached it's reset time and just wasn't removed yet.
        return max(0, rem_seconds)
