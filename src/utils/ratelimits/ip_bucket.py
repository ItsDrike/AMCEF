import logging

from fastapi.requests import Request

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
