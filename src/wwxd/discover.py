"""Find candidate sources for a vault. Nothing is fetched until the user approves it."""

from __future__ import annotations

import email.utils
import hashlib
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from wwxd import ytdl
from wwxd.vault import Source, Vault

logger = logging.getLogger(__name__)

# Titles that usually mean content *about* someone rather than *by* them.
ABOUT_MARKERS = re.compile(
    r"\b(explained|summary|summarized|reacts?|reaction|breakdown|lessons from|what .{1,40} taught|"
    r"analysis|review|book summary|animated|tribute|compilation|clips?|#shorts|top \d+)\b",
    re.IGNORECASE,
)
AUTO_QUERIES = ("{name} interview", "{name} podcast", "{name} talk")


def web_id(url: str) -> str:
    return "web-" + hashlib.sha1(url.encode()).hexdigest()[:12]


def _mentioned_members(text: str, vault: Vault) -> list[str]:
    lowered = text.lower()
    return [m.id for m in vault.members if any(n.lower() in lowered for n in m.names)]


def _hint(title: str, speakers: list[str], own: bool) -> str:
    """own: their channel/site; channel: a group channel with no member named in the title;
    appearance: a member is named; maybe-about: probably commentary on them; unknown."""
    if own:
        return "own"
    if speakers == [] and own is None:
        return "channel"
    if ABOUT_MARKERS.search(title):
        return "maybe-about"
    if speakers:
        return "appearance"
    return "unknown"


def _flat_entries(url: str, limit: int) -> list[dict]:
    with ytdl.new_ydl(extract_flat="in_playlist", skip_download=True, playlistend=limit) as ydl:
        info = ytdl.with_backoff(lambda: ydl.extract_info(url, download=False), "listing videos")
    if not info:
        return []
    entries = info.get("entries")
    if entries is None:
        return [info]
    flat: list[dict] = []
    for entry in entries:
        if not entry:
            continue
        # Channel URLs without a tab expand to nested playlists (Videos, Live, ...).
        if entry.get("_type") == "playlist" or "entries" in entry:
            flat.extend(e for e in entry.get("entries") or [] if e)
        else:
            flat.append(entry)
    return flat[:limit]


def _owners(vault: Vault, configured: list[str] | None) -> list[str]:
    """Who a channel/feed/site belongs to: configured `speakers`, or the only member."""
    if configured:
        return list(configured)
    return [vault.members[0].id] if len(vault.members) == 1 else []


def _youtube_sources(
    vault: Vault, url: str, limit: int, *, own: bool, found_via: str, owners: list[str] | None = None
) -> list[Source]:
    min_duration = vault.discovery.get("min_duration", 240)
    sources = []
    for entry in _flat_entries(url, limit):
        video_id = entry.get("id")
        if not video_id or entry.get("ie_key", "Youtube") != "Youtube":
            continue
        duration = entry.get("duration")
        if duration is not None and duration < min_duration:
            continue
        title = entry.get("title") or video_id
        speakers = _mentioned_members(title, vault)
        if own and not speakers:
            speakers = list(owners or [])
        # In a group vault the shared channel also hosts outside guests.
        hint = _hint(title, speakers, None if own and not speakers else own)
        sources.append(
            Source(
                id=f"yt-{video_id}",
                type="youtube",
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=title,
                hint=hint,
                channel=entry.get("channel") or entry.get("uploader") or "",
                duration=float(duration) if duration else None,
                expected_speakers=speakers,
                found_via=found_via,
            )
        )
    return sources


def _channel_videos_url(url: str) -> str:
    url = url.rstrip("/")
    if re.search(r"/(videos|streams|playlists|podcasts)$", url) or "list=" in url:
        return url
    return url + "/videos"


def _itunes_duration(value: str | None) -> float | None:
    if not value:
        return None
    try:
        seconds = 0.0
        for part in value.strip().split(":"):
            seconds = seconds * 60 + float(part)
        return seconds
    except ValueError:
        return None


def _feed_sources(vault: Vault, url: str, limit: int, *, own: bool = True, owners: list[str] | None = None) -> list[Source]:
    """own: the feed belongs to the member(s). Set `own: false` for someone else's show they guest on."""
    request = urllib.request.Request(url, headers={"User-Agent": "wwxd"})
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())
    atom = "{http://www.w3.org/2005/Atom}"
    channel_title = root.findtext("channel/title") or root.findtext(f"{atom}title") or ""
    items = root.findall("channel/item") or root.findall(f"{atom}entry")
    sources = []
    for item in items[:limit]:
        title = (item.findtext("title") or item.findtext(f"{atom}title") or "").strip()
        link = item.findtext("link") or ""
        if not link:
            link_el = item.find(f"{atom}link")
            link = link_el.get("href", "") if link_el is not None else ""
        date = ""
        raw_date = item.findtext("pubDate")
        if raw_date:
            try:
                date = email.utils.parsedate_to_datetime(raw_date).date().isoformat()
            except (TypeError, ValueError):
                pass
        else:
            date = (item.findtext(f"{atom}published") or item.findtext(f"{atom}updated") or "")[:10]
        mentioned = _mentioned_members(title, vault)
        speakers = mentioned or (list(owners or []) if own else [])
        if not own and not mentioned:
            continue  # someone else's show and the episode doesn't name a member
        hint = "own" if own else _hint(title, mentioned, own=False)
        enclosure = item.find("enclosure")
        if enclosure is not None and (enclosure.get("type") or "").startswith("audio"):
            audio_url = enclosure.get("url", "")
            sources.append(
                Source(
                    id="pod-" + hashlib.sha1(audio_url.encode()).hexdigest()[:12],
                    type="podcast",
                    url=audio_url,
                    title=title,
                    hint=hint,
                    channel=channel_title,
                    date=date,
                    duration=_itunes_duration(item.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}duration")),
                    expected_speakers=speakers,
                    found_via=f"feed:{url}",
                )
            )
        elif link:
            sources.append(
                Source(
                    id=web_id(link),
                    type="web",
                    url=link,
                    title=title,
                    hint=hint,
                    channel=channel_title,
                    date=date,
                    expected_speakers=speakers,
                    found_via=f"feed:{url}",
                )
            )
    return sources


def _link_index_sources(vault: Vault, url: str, pattern: str, limit: int, owners: list[str] | None = None) -> list[Source]:
    request = urllib.request.Request(url, headers={"User-Agent": "wwxd"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    regex = re.compile(pattern)
    seen: set[str] = set()
    sources = []
    for href, label in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL):
        absolute = urllib.parse.urljoin(url, href)
        if absolute in seen or not regex.search(absolute):
            continue
        seen.add(absolute)
        title = re.sub(r"<[^>]+>", "", label).strip()
        sources.append(
            Source(
                id=web_id(absolute),
                type="web",
                url=absolute,
                title=title,
                hint="own",
                expected_speakers=list(owners or []),
                found_via=f"index:{url}",
            )
        )
        if len(sources) >= limit:
            break
    return sources


def discover(vault: Vault, *, per_query: int | None = None) -> tuple[list[Source], list[str]]:
    """Return (new candidate sources, errors). Existing ids, including rejected ones, are skipped."""
    cfg = vault.discovery
    per_query = per_query or cfg.get("per_query", 15)
    errors: list[str] = []
    found: list[Source] = []

    def run(label: str, fn, *args, **kwargs) -> None:
        try:
            found.extend(fn(*args, **kwargs))
        except Exception as exc:  # one broken feed shouldn't stop discovery
            errors.append(f"{label}: {exc}")

    # Channels, feeds and indexes are a URL string or {url: ..., speakers: [member ids]}.
    for channel in cfg.get("youtube_channels") or []:
        url, owners = (channel, None) if isinstance(channel, str) else (channel["url"], channel.get("speakers"))
        run(url, _youtube_sources, vault, _channel_videos_url(url), cfg.get("per_channel", 100),
            own=True, found_via=f"channel:{url}", owners=_owners(vault, owners))

    queries = list(cfg.get("youtube_queries") or [])
    if cfg.get("auto_queries", True):
        for member in vault.members:
            queries.extend(q.format(name=member.name) for q in AUTO_QUERIES)
    for query in queries:
        run(query, _youtube_sources, vault, f"ytsearch{per_query}:{query}", per_query,
            own=False, found_via=f"search:{query}")

    for feed in cfg.get("feeds") or []:
        feed = {"url": feed} if isinstance(feed, str) else feed
        run(feed["url"], _feed_sources, vault, feed["url"], cfg.get("per_feed", 100),
            own=feed.get("own", True), owners=_owners(vault, feed.get("speakers")))

    for index in cfg.get("link_indexes") or []:
        run(index["url"], _link_index_sources, vault, index["url"], index["pattern"], index.get("limit", 500),
            owners=_owners(vault, index.get("speakers")))

    known = {s.id for s in vault.load_sources()}
    new: dict[str, Source] = {}
    for source in found:
        if source.id in known:
            continue
        if source.id in new:
            # Same video from several queries: keep the strongest hint.
            if new[source.id].hint in ("unknown", "maybe-about") and source.hint in ("own", "appearance"):
                new[source.id] = source
            continue
        new[source.id] = source
    return list(new.values()), errors
