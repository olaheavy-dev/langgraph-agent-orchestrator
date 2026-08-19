from taskvault.rate_limit import CAPACITY, RateLimiter


def test_a_fresh_key_may_spend_its_whole_bucket():
    limiter = RateLimiter()
    assert all(limiter.allow('k') for _ in range(CAPACITY))


def test_buckets_are_independent_per_key():
    limiter = RateLimiter()
    for _ in range(CAPACITY):
        limiter.allow('noisy')
    assert limiter.allow('quiet')
