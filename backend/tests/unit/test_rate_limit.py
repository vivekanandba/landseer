"""Unit tests for the fixed-window limiter logic (time injected, no sleeps)."""

from app.rate_limit import _FixedWindowLimiter


def test_allows_up_to_limit_then_blocks():
    limiter = _FixedWindowLimiter()
    # limit=3 within the same window (t=0..)
    assert limiter.check("ip", 3, now=0.0) == (True, 0)
    assert limiter.check("ip", 3, now=0.1)[0] is True
    assert limiter.check("ip", 3, now=0.2)[0] is True
    allowed, retry_after = limiter.check("ip", 3, now=0.3)  # 4th hit
    assert allowed is False
    assert retry_after >= 1


def test_window_resets_after_60s():
    limiter = _FixedWindowLimiter()
    for t in (0.0, 0.1, 0.2, 0.3):
        limiter.check("ip", 3, now=t)
    assert limiter.check("ip", 3, now=0.4)[0] is False
    # A new window starts once 60s have elapsed.
    assert limiter.check("ip", 3, now=61.0) == (True, 0)


def test_keys_are_independent():
    limiter = _FixedWindowLimiter()
    for _ in range(4):
        limiter.check("ip-a", 3, now=0.0)
    # Different client is unaffected by ip-a's usage.
    assert limiter.check("ip-b", 3, now=0.0) == (True, 0)


def test_prune_drops_expired_entries_only():
    limiter = _FixedWindowLimiter()
    limiter.check("old", 3, now=0.0)
    limiter.check("recent", 3, now=59.0)
    limiter._prune(now=61.0)  # 'old' window elapsed, 'recent' still active
    assert "old" not in limiter._hits
    assert "recent" in limiter._hits
