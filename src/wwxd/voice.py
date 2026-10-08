"""Check speaker attribution by voice. Requires the `voice` extra: pip install 'wwxd[voice]'.

For every statement quoted from an audio source, find when the quote is spoken, embed
that stretch of audio with a speaker-verification model, and compare it with each
member's voiceprint. A voiceprint is the robust mean of all statements credited to the
member, so it needs no enrollment as long as most attributions are right; the ones that
aren't stand out.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz

from wwxd import rawdoc
from wwxd.lint import STATEMENT, normalize, parse_citation
from wwxd.rawdoc import parse_timestamp
from wwxd.vault import TIMESTAMPED_PREFIXES, Vault

logger = logging.getLogger(__name__)

MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/{name}"
DEFAULT_MODEL = "nemo_en_titanet_small.onnx"
SAMPLE_RATE = 16000
# Calibrated for TitaNet-small on interview audio: the same speaker scores 0.4 to 0.9,
# a different speaker scores below 0.2.
MISMATCH_BELOW = 0.25
WEAK_BELOW = 0.40
OTHER_MEMBER_MARGIN = 0.15
MIN_SECONDS = 2.0
MAX_SECONDS = 20.0


@dataclass
class Statement:
    page: str
    line: int
    quote: str
    src: str
    ts: str | None
    by: str
    conf: str


def statement_key(src: str, quote: str, by: str) -> str:
    return hashlib.sha1(f"{src}|{normalize(quote)}|{by}".encode()).hexdigest()[:16]


def collect_statements(vault: Vault) -> list[Statement]:
    found = []
    for page in sorted(vault.wiki_dir.rglob("*.md")):
        for line_no, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            match = STATEMENT.match(line)
            cite = parse_citation(match.group("cite")) if match else None
            if not cite or not str(cite["src"]).startswith(TIMESTAMPED_PREFIXES) or not cite.get("by"):
                continue
            found.append(Statement(page.relative_to(vault.path).as_posix(), line_no, match.group("quote"),
                                   cite["src"], cite["ts"], cite["by"], str(cite.get("conf", ""))))
    return found


# --- word timings -----------------------------------------------------------------

def words_from_json3(data: dict) -> list[tuple[float, str]]:
    """(seconds, normalized word) for every word in a YouTube json3 caption track."""
    words = []
    for event in data.get("events") or []:
        if event.get("aAppend") or "segs" not in event:
            continue
        start = event.get("tStartMs", 0)
        for seg in event["segs"]:
            for word in normalize(seg.get("utf8", "")).split():
                words.append(((start + seg.get("tOffsetMs", 0)) / 1000.0, word))
    return words


def words_from_raw(doc: rawdoc.RawDoc) -> list[tuple[float, str]]:
    """Fallback: spread each paragraph's words evenly until the next paragraph starts."""
    words = []
    for i, seg in enumerate(doc.segments):
        tokens = normalize(seg.text).split()
        end = doc.segments[i + 1].start if i + 1 < len(doc.segments) else seg.start + 30.0
        step = (end - seg.start) / max(len(tokens), 1)
        words.extend((seg.start + k * step, w) for k, w in enumerate(tokens))
    return words


def locate(words: list[tuple[float, str]], quote: str, ts: str | None) -> tuple[float, float] | None:
    """Time span of the quote's first part, searched near its timestamp."""
    part = normalize(re.split(r"\.\.\.|…", quote)[0])
    lo, hi = 0, len(words)
    if ts:
        at = parse_timestamp(ts)
        lo = next((i for i, (t, _) in enumerate(words) if t >= at - 60), 0)
        hi = next((i for i, (t, _) in enumerate(words) if t > at + 120), len(words))
    text, starts = "", []
    for i in range(lo, hi):
        starts.append(len(text))
        text += words[i][1] + " "
    if not part or not text:
        return None
    hit = fuzz.partial_ratio_alignment(part, text)
    if hit is None or hit.score < 85:
        return None
    first = lo + max(k for k, c in enumerate(starts) if c <= hit.dest_start)
    last = lo + max(k for k, c in enumerate(starts) if c <= max(hit.dest_end - 1, 0))
    end = words[last + 1][0] if last + 1 < len(words) else words[last][0] + 1.0
    return words[first][0], end + 0.3


# --- audio ------------------------------------------------------------------------

def load_audio(path: Path):
    import av
    import numpy as np

    chunks = []
    with av.open(str(path)) as container:
        resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
        for frame in container.decode(container.streams.audio[0]):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray().reshape(-1))
    return np.concatenate(chunks) if chunks else np.zeros(0, dtype="float32")


class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL, cache: Path | None = None):
        try:
            import sherpa_onnx
        except ImportError as exc:
            raise RuntimeError("The voice check needs the voice extra: pip install 'wwxd[voice]'") from exc
        cache = cache or Path.home() / ".cache" / "wwxd" / "models"
        cache.mkdir(parents=True, exist_ok=True)
        path = cache / model_name
        if not path.exists():
            logger.warning("Downloading speaker model %s", model_name)
            urllib.request.urlretrieve(MODEL_URL.format(name=model_name), path)
        config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=str(path), num_threads=4)
        self.extractor = sherpa_onnx.SpeakerEmbeddingExtractor(config)
        self.model_name = model_name

    def __call__(self, audio, start: float, end: float):
        import numpy as np

        start = max(0.0, start - 0.1)
        end = min(max(end, start + MIN_SECONDS), start + MAX_SECONDS)
        stream = self.extractor.create_stream()
        stream.accept_waveform(SAMPLE_RATE, audio[int(start * SAMPLE_RATE) : int(end * SAMPLE_RATE)])
        stream.input_finished()
        vec = np.array(self.extractor.compute(stream))
        return vec / (np.linalg.norm(vec) or 1.0)


def _youtube_words(video_id: str, cache: Path) -> list[tuple[float, str]] | None:
    path = cache / f"{video_id}.json3"
    if not path.exists():
        import yt_dlp

        from wwxd.fetchers.youtube import YDL_BASE, _pick_caption_track, video_url

        with yt_dlp.YoutubeDL(YDL_BASE) as ydl:
            info = ydl.extract_info(video_url(video_id), download=False)
            track = _pick_caption_track(info)
            fmt = next((f for f in (track[1] if track else []) if f.get("ext") == "json3"), None)
            if fmt is None:
                return None
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(ydl.urlopen(fmt["url"]).read())
    return words_from_json3(json.loads(path.read_text(encoding="utf-8")))


def _audio_path(vault: Vault, src: str) -> Path:
    from wwxd.fetchers import whisper

    directory = vault.cache_dir / "audio"
    if src.startswith("yt-"):
        video_id = src.removeprefix("yt-")
        return whisper.download_youtube_audio(f"https://www.youtube.com/watch?v={video_id}", video_id, directory)
    url = next(s.url for s in vault.load_sources() if s.id == src)
    return whisper.download_audio_url(url, src, directory)


# --- scoring ----------------------------------------------------------------------

def voiceprints(embeddings: dict[str, list]) -> dict:
    """Robust mean per member: drop the least similar 30% three times, so wrong attributions don't shape it."""
    import numpy as np

    prints = {}
    for member, vecs in embeddings.items():
        matrix = np.array(vecs)
        keep = np.arange(len(matrix))
        for _ in range(3):
            centre = matrix[keep].mean(0)
            centre /= np.linalg.norm(centre) or 1.0
            sims = matrix @ centre
            keep = np.where(sims >= np.percentile(sims, 30))[0] if len(matrix) >= 4 else keep
        prints[member] = centre
    return prints


def verdict(own: float, others: dict[str, float]) -> tuple[str, str]:
    best_other, other_sim = max(others.items(), key=lambda kv: kv[1]) if others else ("", -1.0)
    if other_sim - own >= OTHER_MEMBER_MARGIN and other_sim >= WEAK_BELOW:
        return "mismatch", best_other
    if own < MISMATCH_BELOW:
        return "mismatch", ""
    if own < WEAK_BELOW:
        return "weak", ""
    return "match", ""


def check(vault: Vault, *, ids: list[str] | None = None, model_name: str = DEFAULT_MODEL) -> list[dict]:
    statements = collect_statements(vault)
    sources = sorted({s.src for s in statements if not ids or s.src in ids})
    embed = Embedder(model_name)
    timing_cache = vault.cache_dir / "timing"
    spans: dict[int, tuple[float, float]] = {}
    vectors: dict[int, object] = {}
    for n, src in enumerate(sources, 1):
        logger.warning("[%d/%d] %s", n, len(sources), src)
        try:
            words = _youtube_words(src.removeprefix("yt-"), timing_cache) if src.startswith("yt-") else None
            words = words or words_from_raw(rawdoc.read(vault.raw_path(src)))
            audio = load_audio(_audio_path(vault, src))
        except Exception as exc:
            logger.warning("  skipped %s: %s", src, exc)
            continue
        for i, st in enumerate(statements):
            if st.src != src:
                continue
            found = locate(words, st.quote, st.ts)
            if found:
                spans[i] = found
                vectors[i] = embed(audio, *found)
    by_member: dict[str, list] = {}
    for i, vec in vectors.items():
        by_member.setdefault(statements[i].by, []).append(vec)
    prints = voiceprints(by_member)
    results = []
    for i, st in enumerate(statements):
        if st.src not in sources:
            continue
        row = {"key": statement_key(st.src, st.quote, st.by), "page": st.page, "line": st.line, "src": st.src,
               "ts": st.ts, "by": st.by, "conf": st.conf, "quote": st.quote, "model": model_name}
        if i not in vectors or st.by not in prints:
            row.update(voice="unchecked", reason="quote not located in the audio" if i not in vectors else "no voiceprint")
        else:
            own = float(vectors[i] @ prints[st.by])
            others = {m: float(vectors[i] @ p) for m, p in prints.items() if m != st.by}
            label, other = verdict(own, others)
            start, end = spans[i]
            row.update(voice=label, own=round(own, 3), others={m: round(v, 3) for m, v in others.items()},
                       sounds_like=other, span=[round(start, 1), round(end, 1)])
        results.append(row)
    return results


def save(vault: Vault, results: list[dict]) -> Path:
    """Merge results into attribution.jsonl, keyed by statement."""
    path = vault.path / "attribution.jsonl"
    merged = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            merged[row["key"]] = row
    for row in results:
        merged[row["key"]] = {**merged.get(row["key"], {}), **row}
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged.values()), encoding="utf-8")
    return path


def load(vault: Vault) -> dict[str, dict]:
    path = vault.path / "attribution.jsonl"
    if not path.exists():
        return {}
    return {row["key"]: row for row in map(json.loads, path.read_text(encoding="utf-8").splitlines())}
