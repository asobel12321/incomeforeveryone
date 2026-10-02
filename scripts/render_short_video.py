#!/usr/bin/env python3
"""Render a reviewable 9:16 MP4 from a post's video_script front matter."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
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


def make_ass(title: str, post_date: str, script: str, duration: float, *, ai_voice: bool,
             stories: list[str] | None = None) -> str:
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
    for index, chunk in enumerate(chunks):
        start = elapsed
        elapsed += duration * len(chunk.split()) / total_words
        end = duration if index == len(chunks) - 1 else elapsed
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
    title, post_date, script, stories = read_article(POST_DIR / f"{args.date}.md")
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
    (work_dir / "captions.ass").write_text(
        make_ass(title, post_date, script, duration, ai_voice=bool(audio and not args.audio), stories=stories),
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
