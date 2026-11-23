"""Transcribe an audio/video file with faster-whisper and write a Word document."""

from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt
from faster_whisper import WhisperModel

MODELS = ["tiny", "base", "small", "medium", "large-v3"]


def format_time(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def transcribe(audio_path, model_name="small", language=None, on_status=None, on_progress=None, is_cancelled=None):
    """Return (segments, info). segments is a list of (start, end, text).

    on_progress receives a 0-100 int. is_cancelled is polled between segments.
    """
    on_status = on_status or (lambda _msg: None)
    on_progress = on_progress or (lambda _pct: None)
    is_cancelled = is_cancelled or (lambda: False)

    on_status("Preparing speech model (the first time, this downloads a few hundred MB, please wait)...")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    on_status("Transcribing...")
    segments_iter, info = model.transcribe(
        str(audio_path), language=language, vad_filter=True, beam_size=5
    )

    segments = []
    for seg in segments_iter:
        if is_cancelled():
            raise InterruptedError("Cancelled")
        text = seg.text.strip()
        if text:
            segments.append((seg.start, seg.end, text))
        if info.duration:
            on_progress(min(99, int(seg.end / info.duration * 100)))
    on_progress(100)
    return segments, info


def write_docx(segments, source_path, output_path, include_timestamps=True, language=None, duration=None):
    source_path = Path(source_path)
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    doc.add_heading(f"Transcript: {source_path.stem}", level=1)
    meta = [f"Source file: {source_path.name}", f"Generated: {datetime.now():%Y-%m-%d %H:%M}"]
    if language:
        meta.append(f"Language: {language}")
    if duration:
        meta.append(f"Duration: {format_time(duration)}")
    doc.add_paragraph("\n".join(meta)).runs[0].italic = True

    if include_timestamps:
        for start, _end, text in segments:
            p = doc.add_paragraph()
            stamp = p.add_run(f"[{format_time(start)}] ")
            stamp.bold = True
            p.add_run(text)
    else:
        doc.add_paragraph(" ".join(text for _s, _e, text in segments))

    doc.save(str(output_path))
