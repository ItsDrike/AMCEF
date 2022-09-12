import logging

from fastapi.requests import Request
from fastapi.responses import Response

from src.utils.ratelimits.abc import RedisBucketBase

log = logging.getLogger(__name__)


class IPRedisBucket(RedisBucketBase[str]):
    """A per IP request bucket backed by Redis."""

    async def get_bucket_key(self, request: Request) -> str:
        """Obtain the IP address from request as the bucket key."""
        if request.client is None:
            raise ValueError("Unable to obtain client's IP.")

        host_address, _ = request.client.host
        log.debug(f"Obtained bucket key for rate-limited route: {host_address} (bucket #{self.bucket_no})")
        return host_address

    async def add_headers(self, response: Response, bucket_key: str) -> None:
        """
        Override add_headers since we don't want to be informing the user about ip-based rate-limits.

        This also allows us to use this bucket in combination with other buckets, as it won't be
        overriding headers from them.
        """

    async def add_cooldown_headers(self, response: Response, remaining_seconds: int) -> None:
        """
        Override add_cooldown_headers to change the cooldown header name.

        This avoids conflicts with other buckets, and makes it clear that if this header appears,
        the API is under a ip-wide cooldown which should be respected.
        """
        response.headers.append("Ip-Cooldown-Reset", str(remaining_seconds))
