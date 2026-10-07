from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TIMESTAMP_LINE = re.compile(r"^\[(\d+(?::\d{2}){1,2})\]\s?(.*)$")


@dataclass
class Segment:
    start: float
    text: str


@dataclass
class RawDoc:
    meta: dict
    segments: list[Segment] = field(default_factory=list)  # timestamped sources
    body: str = ""  # untimed sources (articles, files)


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def parse_timestamp(value: str) -> float:
    seconds = 0
    for part in value.split(":"):
        seconds = seconds * 60 + int(part)
    return float(seconds)


def chunk_segments(segments: list[Segment], target_seconds: float = 30.0) -> list[Segment]:
    """Merge short caption segments into ~30s paragraphs, splitting at segment boundaries."""
    chunks: list[Segment] = []
    current: list[str] = []
    start: float | None = None
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        if start is None:
            start = seg.start
        current.append(text)
        if seg.start - start >= target_seconds:
            chunks.append(Segment(start, " ".join(current)))
            current, start = [], None
    if current and start is not None:
        chunks.append(Segment(start, " ".join(current)))
    return chunks


def render(doc: RawDoc) -> str:
    front = yaml.safe_dump(doc.meta, sort_keys=False, allow_unicode=True, width=120).strip()
    if doc.segments:
        body = "\n\n".join(
            f"[{format_timestamp(c.start)}] {c.text}" for c in chunk_segments(doc.segments)
        )
    else:
        body = doc.body.strip()
    return f"---\n{front}\n---\n{body}\n"


def write(doc: RawDoc, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(doc), encoding="utf-8")


def read(path: Path) -> RawDoc:
    text = path.read_text(encoding="utf-8")
    meta: dict = {}
    if text.startswith("---\n"):
        _, front, text = text.split("---\n", 2)
        meta = yaml.safe_load(front) or {}
    segments: list[Segment] = []
    for para in text.split("\n\n"):
        match = TIMESTAMP_LINE.match(para.strip())
        if match:
            segments.append(Segment(parse_timestamp(match.group(1)), match.group(2)))
    if segments:
        return RawDoc(meta=meta, segments=segments)
    return RawDoc(meta=meta, body=text)
