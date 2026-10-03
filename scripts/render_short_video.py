#!/usr/bin/env python3
"""Render a reviewable 9:16 MP4 from a post's video_script front matter."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date
from pathlib import Path

from generate_daily_post import POST_DIR
from generate_video_script import FRONT_MATTER, WORD


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "video-preview"
SPEECH_MODEL = "gpt-4o-mini-tts"
SPEECH_VOICE = "marin"
SPEECH_STYLE = (
    "Warm, grounded educational narrator. Speak conversationally at a measured pace, "
    "with brief pauses between ideas. Give numbers and worker impact gentle emphasis. "
    "Avoid a dramatic announcer tone."
)
TRANSCRIPTION_MODEL = "whisper-1"


def read_article(path: Path) -> tuple[str, str, str, list[str]]:
    article = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = FRONT_MATTER.match(article)
    if not match:
        raise ValueError(f"Missing YAML front matter: {path}")
    front = match.group(1)
    title_match = re.search(r'^title:\s*"([^"]+)"\s*$', front, re.M)
    date_match = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})\s*$", front, re.M)
    script_match = re.search(r"(?m)^video_script:\s*[>|][-+]?\s*\n((?:[ \t]+[^\n]*\n?)+)", front)
    if not title_match or not date_match or not script_match:
        raise ValueError(f"Article needs title, date, and video_script: {path}")
    script = re.sub(r"\s+", " ", script_match.group(1)).strip()
    if not 75 <= len(WORD.findall(script)) <= 130:
        raise ValueError("Article video_script must contain 75–130 spoken words")
    stories = re.findall(r"(?m)^- \*\*(.+?)\*\*", article[match.end():])[:3]
    return title_match.group(1), date_match.group(1), script, stories


def synthesize_speech(script: str, destination: Path, *, model: str, voice: str,
                      style: str = SPEECH_STYLE) -> None:
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for AI narration; use --audio or --silent")
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps({
            "model": model,
            "voice": voice,
            "input": script,
            "instructions": style,
            "response_format": "mp3",
        }).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            destination.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Speech API returned HTTP {exc.code}") from exc


def probe_duration(audio: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def fit_ai_audio(audio: Path) -> tuple[Path, float]:
    duration = probe_duration(audio)
    target = min(59.0, max(31.0, duration))
    if target == duration:
        return audio, duration
    adjusted = audio.with_name("narration-fitted.mp3")
    speed = duration / target
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(audio),
         "-filter:a", f"atempo={speed:.6f}", "-c:a", "libmp3lame", "-q:a", "3", str(adjusted)],
        check=True,
    )
    return adjusted, probe_duration(adjusted)


def ass_time(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, remainder = divmod(centiseconds, 360000)
    minutes, remainder = divmod(remainder, 6000)
    whole_seconds, hundredths = divmod(remainder, 100)
    return f"{hours}:{minutes:02}:{whole_seconds:02}.{hundredths:02}"


def ass_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", r"\N")


def wrap_words(value: str, width: int, max_lines: int | None = None) -> str:
    lines: list[str] = []
    current = ""
    for word in value.split():
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if max_lines and len(lines) > max_lines:
        raise ValueError("Article title is too long for the video layout")
    return r"\N".join(ass_escape(line) for line in lines)


def caption_chunks(script: str, words_per_chunk: int = 9) -> list[str]:
    words = script.split()
    return [" ".join(words[index:index + words_per_chunk]) for index in range(0, len(words), words_per_chunk)]


def story_cards(path: Path) -> list[tuple[str, str]]:
    """Extract short fact text and source hosts from the three published story blocks."""
    article = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    section = article.split("### Key Stories", 1)
    if len(section) != 2:
        return []
    cards = []
    for block in re.split(r"(?m)^- \*\*", section[1].split("\n---", 1)[0])[1:4]:
        lines = block.splitlines()
        summary = re.sub(r"\s+", " ", " ".join(
            line.strip() for line in lines[1:] if line.strip() and not line.lstrip().startswith("[")
        )).strip()
        urls = re.findall(r"\]\((https?://[^)]+)\)", block)
        source = urllib.parse.urlparse(urls[-1]).hostname or "" if urls else ""
        source = source.removeprefix("www.")
        context = summary
        for delimiter in (", ", ". ", " and "):
            if delimiter not in summary:
                continue
            candidate = summary.split(delimiter, 1)[0]
            if 5 <= len(candidate.split()) <= 25:
                context = candidate
                break
        if len(context.split()) > 25:
            context = " ".join(context.split()[:25]) + "…"
        number = re.search(r"(?<!\w)(?:\$)?\d[\d,.]*(?:%|\s+(?:million|billion|jobs))?", summary)
        if number and number.group(0).strip() in context:
            value = number.group(0).strip()
            fact = f"{value}|{context}"
        else:
            fact = context
        cards.append((fact, source))
    return cards


def transcribe_word_timing(audio: Path, script: str) -> list[tuple[str, float, float]]:
    """Use the rendered narration itself to locate caption words."""
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for audio-aligned captions")
    boundary = f"----ife-{uuid.uuid4().hex}"
    fields = (("model", TRANSCRIPTION_MODEL), ("response_format", "verbose_json"),
              ("timestamp_granularities[]", "word"))
    body = bytearray()
    for name, value in fields:
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    body.extend(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"{audio.name}\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode()
    )
    body.extend(audio.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions", data=bytes(body),
        headers={"Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.load(response)
    words = [(item["word"].strip(), float(item["start"]), float(item["end"]))
             for item in result.get("words", []) if item.get("word", "").strip()]
    spoken = " ".join(word for word, _, _ in words)
    normalize = lambda value: " ".join(re.findall(r"[\w]+", value.casefold()))
    if not words or difflib.SequenceMatcher(None, normalize(script), normalize(spoken)).ratio() < 0.78:
        raise ValueError("Transcribed narration differs too much from the article script")
    if any(end <= start or start < 0 for _, start, end in words):
        raise ValueError("Transcription contains invalid timestamps")
    return words


def timed_caption_chunks(words: list[tuple[str, float, float]], duration: float,
                         words_per_chunk: int = 8) -> list[tuple[str, float, float]]:
    cues = []
    for index in range(0, len(words), words_per_chunk):
        group = words[index:index + words_per_chunk]
        start = max(0.0, group[0][1] - 0.08)
        end = min(duration, group[-1][2] + 0.12)
        if cues:
            start = max(start, cues[-1][2])
        if end > start:
            cues.append((" ".join(word for word, _, _ in group), start, end))
    return cues


def make_ass(title: str, post_date: str, script: str, duration: float, *, ai_voice: bool,
             stories: list[str] | None = None, cards: list[tuple[str, str]] | None = None,
             caption_cues: list[tuple[str, float, float]] | None = None) -> str:
    if not 30 <= duration <= 60:
        raise ValueError(f"Narration must run 30–60 seconds; got {duration:.1f} seconds")
    display_date = date.fromisoformat(post_date).strftime("%B %d, %Y").replace(" 0", " ")
    chunks = caption_chunks(script)
    total_words = sum(len(chunk.split()) for chunk in chunks)
    elapsed = 0.0
    events = [
        f"Dialogue: 0,{ass_time(0)},{ass_time(duration)},Brand,,0,0,0,,INCOME FOR EVERYONE",
        f"Dialogue: 0,{ass_time(0)},{ass_time(duration)},Footer,,0,0,0,,{ass_escape(display_date)}  •  incomeforeveryone.org",
    ]
    if len(stories or []) == 3:
        intro = min(5.0, duration * 0.15)
        outro = min(5.0, duration * 0.15)
        scene_length = (duration - intro - outro) / 3
        events.append(
            f"Dialogue: 0,{ass_time(0)},{ass_time(intro)},Title,,0,0,0,,"
            r"{\move(70,300,70,235,0,700)\fad(250,450)}" + wrap_words(title, 30, 4)
        )
        events.append(
            f"Dialogue: 0,{ass_time(0)},{ass_time(intro)},SceneLabel,,0,0,0,,"
            r"{\fad(350,450)}THREE STORIES TO KNOW"
        )
        for number, headline in enumerate(stories, 1):
            start = intro + (number - 1) * scene_length
            end = intro + number * scene_length
            events.append(
                f"Dialogue: 0,{ass_time(start)},{ass_time(end)},SceneNumber,,0,0,0,,"
                r"{\move(-260,515,70,515,0,650)\fad(200,350)}" + f"0{number} / 03"
            )
            events.append(
                f"Dialogue: 0,{ass_time(start)},{ass_time(end)},SceneTitle,,0,0,0,,"
                r"{\move(1180,670,70,670,0,700)\fad(150,350)}" + wrap_words(headline, 28, 4)
            )
            progress = "  ".join("●" if index <= number else "○" for index in range(1, 4))
            events.append(
                f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Progress,,0,0,0,,"
                r"{\fad(250,350)}" + progress
            )
            if cards and len(cards) >= number:
                fact, source = cards[number - 1]
                if "|" in fact:
                    value, context = fact.split("|", 1)
                    events.append(
                        f"Dialogue: 0,{ass_time(start)},{ass_time(end)},FactNumber,,0,0,0,,"
                        r"{\move(1150,930,70,930,0,650)\fad(150,350)}" + ass_escape(value)
                    )
                    fact = context
                events.append(
                    f"Dialogue: 0,{ass_time(start)},{ass_time(end)},FactText,,0,0,0,,"
                    r"{\fad(450,350)}" + wrap_words(fact, 34)
                )
                if source:
                    events.append(
                        f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Source,,0,0,0,,"
                        r"{\fad(450,350)}SOURCE: " + ass_escape(source)
                    )
        last_sentence = re.split(r"(?<=[.!?])\s+", script.strip())[-1]
        events.append(
            f"Dialogue: 0,{ass_time(duration - outro)},{ass_time(duration)},SceneNumber,,0,0,0,,"
            r"{\fad(300,300)}WHY IT MATTERS"
        )
        events.append(
            f"Dialogue: 0,{ass_time(duration - outro)},{ass_time(duration)},SceneTitle,,0,0,0,,"
            r"{\move(1180,670,70,670,0,700)\fad(150,250)}" + wrap_words(last_sentence, 28, 5)
        )
    else:
        events.append(
            f"Dialogue: 0,{ass_time(0)},{ass_time(duration)},Title,,0,0,0,,{wrap_words(title, 30, 4)}"
        )
    if ai_voice:
        events.append(f"Dialogue: 0,{ass_time(0)},{ass_time(duration)},Disclosure,,0,0,0,,AI-generated narration")
    if caption_cues is None:
        caption_cues = []
        for index, chunk in enumerate(chunks):
            start = elapsed
            elapsed += duration * len(chunk.split()) / total_words
            end = duration if index == len(chunks) - 1 else elapsed
            caption_cues.append((chunk, start, end))
    for chunk, start, end in caption_cues:
        events.append(f"Dialogue: 1,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{wrap_words(chunk, 24)}")
    return """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Brand,Arial,34,&H00A3E4C2,&H00A3E4C2,&H000C1820,&H000C1820,1,0,0,0,100,100,2,0,1,0,0,7,70,70,85,1
Style: Title,Arial,62,&H00FFFFFF,&H00FFFFFF,&H000C1820,&H000C1820,1,0,0,0,100,100,0,0,1,0,0,7,70,70,235,1
Style: SceneLabel,Arial,38,&H00A3E4C2,&H00A3E4C2,&H000C1820,&H000C1820,1,0,0,0,100,100,2,0,1,0,0,7,70,70,690,1
Style: SceneNumber,Arial,42,&H00A3E4C2,&H00A3E4C2,&H000C1820,&H000C1820,1,0,0,0,100,100,2,0,1,0,0,7,70,70,515,1
Style: SceneTitle,Arial,58,&H00FFFFFF,&H00FFFFFF,&H000C1820,&H000C1820,1,0,0,0,100,100,0,0,1,0,0,7,70,70,670,1
Style: FactNumber,Arial,92,&H00A3E4C2,&H00A3E4C2,&H000C1820,&H000C1820,1,0,0,0,100,100,0,0,1,0,0,7,70,70,930,1
Style: FactText,Arial,38,&H00FFFFFF,&H00FFFFFF,&H000C1820,&H000C1820,0,0,0,0,100,100,0,0,1,0,0,7,70,70,1040,1
Style: Source,Arial,27,&H00C8D4D2,&H00C8D4D2,&H000C1820,&H000C1820,0,0,0,0,100,100,0,0,1,0,0,7,70,70,1250,1
Style: Progress,Arial,46,&H00A3E4C2,&H00A3E4C2,&H000C1820,&H000C1820,1,0,0,0,100,100,2,0,1,0,0,8,70,70,505,1
Style: Caption,Arial,64,&H00FFFFFF,&H00FFFFFF,&H000C1820,&HAA0C1820,1,0,0,0,100,100,0,0,3,8,1,2,68,68,405,1
Style: Footer,Arial,30,&H00C8D4D2,&H00C8D4D2,&H000C1820,&H000C1820,0,0,0,0,100,100,0,0,1,0,0,2,60,60,80,1
Style: Disclosure,Arial,28,&H00C8D4D2,&H00C8D4D2,&H000C1820,&H000C1820,0,0,0,0,100,100,0,0,1,0,0,9,60,60,85,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n"


def render_video(work_dir: Path, duration: float, audio: Path | None) -> Path:
    output = work_dir / "video.mp4"
    inputs = ["-f", "lavfi", "-i", "color=c=0x10222a:s=1080x1920:r=30"]
    if audio:
        inputs += ["-i", str(audio.resolve())]
    else:
        inputs += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
               "-vf", "ass=captions.ass", "-t", str(duration), "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "video.mp4"]
    subprocess.run(command, cwd=work_dir, check=True)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Article date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    audio_group = parser.add_mutually_exclusive_group()
    audio_group.add_argument("--audio", type=Path, help="Use a recorded MP3/WAV narration")
    audio_group.add_argument("--silent", action="store_true", help="Create a caption-only draft")
    parser.add_argument("--voice", default=SPEECH_VOICE)
    parser.add_argument("--voice-style", default=SPEECH_STYLE,
                        help="Delivery instructions for AI narration")
    parser.add_argument("--speech-model", default=SPEECH_MODEL)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        parser.error("Date must be YYYY-MM-DD")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("ffmpeg and ffprobe are required")
    article_path = POST_DIR / f"{args.date}.md"
    title, post_date, script, stories = read_article(article_path)
    cards = story_cards(article_path)
    work_dir = args.output_dir.resolve() / args.date
    work_dir.mkdir(parents=True, exist_ok=True)
    if args.audio:
        audio = args.audio.resolve()
        if not audio.is_file():
            raise FileNotFoundError(audio)
    elif args.silent:
        audio = None
    else:
        audio = work_dir / "narration.mp3"
        synthesize_speech(script, audio, model=args.speech_model, voice=args.voice,
                          style=args.voice_style)
    if audio and not args.audio:
        audio, duration = fit_ai_audio(audio)
    else:
        duration = probe_duration(audio) if audio else len(WORD.findall(script)) * 60 / 140
    if not 30 <= duration <= 60:
        raise ValueError(f"Narration duration must be 30–60 seconds; got {duration:.1f}")
    caption_cues = None
    if audio and not args.audio:
        try:
            words = transcribe_word_timing(audio, script)
            caption_cues = timed_caption_chunks(words, duration)
        except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError) as exc:
            print(f"warning: audio-aligned captions unavailable ({exc}); using estimated timing", file=sys.stderr)
    (work_dir / "captions.ass").write_text(
        make_ass(title, post_date, script, duration, ai_voice=bool(audio and not args.audio),
                 stories=stories, cards=cards, caption_cues=caption_cues),
        encoding="utf-8",
    )
    video = render_video(work_dir, duration, audio)
    print(video)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
