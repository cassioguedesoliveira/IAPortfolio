class ProviderError(Exception):
    """An upstream LLM provider failed. ``retryable`` tells the gateway whether trying again can help."""

    def __init__(self, message: str, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.attempts = 1


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: float) -> None:
        super().__init__(f"rate limit exceeded, retry in {retry_after:.1f}s")
        self.retry_after = retry_after


class AllProvidersFailed(Exception):
    def __init__(self, failures: dict[str, str]) -> None:
        super().__init__(f"all providers failed: {failures}")
        self.failures = failures
