import logging

from fastapi.requests import Request

from src.utils.ratelimits.abc import RedisBucketBase

log = logging.getLogger(__name__)


class MemberRedisBucket(RedisBucketBase[int]):
    """
    A per member request bucket backed by Redis.

    Since this is a per-member bucket, we need to be able to identify the member
    from a request. This can therefore only be used with routes with a middleware
    which adds a member_id attribute, which we can use as the bucket keys.
    """

    async def get_bucket_key(self, request: Request) -> int:
        """Obtain user_id from request as the bucket key."""
        if not hasattr(request.state, "user_id"):
            raise ValueError("User-Bucket can only work with JWTBearer routes.")
        bucket_key = request.state.user_id
        log.debug(f"Obtained bucket key for rate-limited route: {bucket_key} (bucket #{self.bucket_no})")
        return bucket_key
