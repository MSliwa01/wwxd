import urllib.error

import pytest
from yt_dlp.utils import DownloadError, ExtractorError

from wwxd import ytdl

RATE_LIMITED = "ERROR: [youtube] abcdefghijk: Unable to download API page: HTTP Error 429: Too Many Requests"


class Flaky:
    """Raises the given errors in turn, then returns 'ok'."""

    def __init__(self, *errors: Exception):
        self.errors = list(errors)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return "ok"


def test_retries_429_with_growing_capped_waits(capsys):
    waits: list[float] = []
    fn = Flaky(DownloadError(RATE_LIMITED), DownloadError(RATE_LIMITED), DownloadError(RATE_LIMITED))
    assert ytdl.with_backoff(fn, "reading video info", sleep=waits.append) == "ok"
    assert fn.calls == 4
    for attempt, wait in enumerate(waits):
        low = ytdl.RATE_LIMIT_BASE * 2**attempt
        assert min(low, 60) <= wait <= min(low * 1.5, 60)
    notices = capsys.readouterr().err.strip().splitlines()
    assert len(notices) == 3
    assert "HTTP 429" in notices[0] and "retry 1/3" in notices[0]


def test_gives_up_with_a_hint():
    waits: list[float] = []
    fn = Flaky(*[DownloadError(RATE_LIMITED)] * 5)
    with pytest.raises(RuntimeError, match="still rate limited after 3 retries"):
        ytdl.with_backoff(fn, "listing videos", sleep=waits.append)
    assert len(waits) == 3


def test_other_errors_are_not_retried_by_default():
    waits: list[float] = []
    fn = Flaky(DownloadError("ERROR: [youtube] abcdefghijk: Video unavailable"))
    with pytest.raises(DownloadError):
        ytdl.with_backoff(fn, "reading video info", sleep=waits.append)
    assert waits == [] and fn.calls == 1


def test_retry_other_uses_the_short_delay(monkeypatch):
    monkeypatch.setenv("WWXD_DOWNLOAD_DELAY", "2")
    waits: list[float] = []
    fn = Flaky(OSError("connection reset"), OSError("connection reset"))
    assert ytdl.with_backoff(fn, "downloading captions", retry_other=True, sleep=waits.append) == "ok"
    assert waits == [2.0, 4.0]


class FakeHTTPError(Exception):
    def __init__(self, status: int):
        super().__init__("boom")
        self.status = status


def test_detects_429_wrapped_in_yt_dlp_errors():
    inner = ExtractorError("Unable to download webpage", cause=FakeHTTPError(429))
    outer = DownloadError("ERROR: something went wrong", exc_info=(type(inner), inner, None))
    assert ytdl.is_rate_limited(outer)
    plain = ExtractorError("Unable to download webpage", cause=FakeHTTPError(403))
    assert not ytdl.is_rate_limited(DownloadError("ERROR: forbidden", exc_info=(type(plain), plain, None)))


def test_detects_urllib_and_chained_errors():
    http = urllib.error.HTTPError("https://example.com", 429, "Too Many Requests", None, None)
    assert ytdl.is_rate_limited(http)
    try:
        try:
            raise FakeHTTPError(429)
        except FakeHTTPError as exc:
            raise RuntimeError("caption download failed") from exc
    except RuntimeError as wrapped:
        assert ytdl.is_rate_limited(wrapped)


def test_video_ids_with_429_are_not_rate_limits():
    assert not ytdl.is_rate_limited(DownloadError("ERROR: [youtube] ab429cd-429: Video unavailable"))


def test_backoff_delay_is_capped():
    assert ytdl.backoff_delay(0, rand=lambda: 0.0) == ytdl.RATE_LIMIT_BASE
    assert ytdl.backoff_delay(1, rand=lambda: 1.0) == ytdl.RATE_LIMIT_BASE * 3
    assert ytdl.backoff_delay(10, rand=lambda: 1.0) == ytdl.RATE_LIMIT_CAP


def test_caption_download_backs_off(monkeypatch):
    from wwxd.fetchers.youtube import _download_captions

    waits: list[float] = []
    monkeypatch.setattr(ytdl.time, "sleep", waits.append)
    body = b'{"events": [{"tStartMs": 0, "segs": [{"utf8": "hello"}]}]}'

    class Response:
        def read(self):
            return body

    class FakeYDL:
        calls = 0

        def urlopen(self, url):
            FakeYDL.calls += 1
            if FakeYDL.calls == 1:
                raise FakeHTTPError(429)
            return Response()

    segments = _download_captions(FakeYDL(), [{"ext": "json3", "url": "https://example.com/c"}])
    assert [s.text for s in segments] == ["hello"]
    assert len(waits) == 1 and waits[0] >= ytdl.RATE_LIMIT_BASE
