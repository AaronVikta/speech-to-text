# Recording to Word

A desktop app that turns an audio or video recording into a Word (`.docx`) transcript.
It uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and runs fully offline on the CPU once the model has been downloaded.

## Features

- Pick a file or drag and drop it: mp3, wav, m4a, flac, ogg, opus, aac, wma, mp4, mkv, mov or webm
- Model choice: `tiny`, `base`, `small` (default), `medium`, `large-v3`. Larger models are more accurate but slower.
- Detects the language automatically, or you can pick one
- Optional timestamps in the transcript
- Shows progress and lets you cancel

## Requirements

- Linux, with a desktop session (Wayland or X11)
- **Python 3.13.** Use 3.13 or older, not 3.14 or newer: the pinned `av<17` has no prebuilt wheels for newer Pythons, and building it from source fails.
- [uv](https://docs.astral.sh/uv/) (recommended), to get the right Python without changing the system one

## Setup

```bash
# Install uv (one time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create the virtualenv with Python 3.13 and install dependencies
uv venv -p 3.13 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements.txt
```

## Run

```bash
./run.sh
```

or `.venv/bin/python app.py`.

The first transcription with a given model downloads it from Hugging Face (from about 75 MB for `tiny` to about 3 GB for `large-v3`). Later runs use the cached copy.

## Files

- `app.py`: PySide6 GUI
- `transcriber.py`: transcription (faster-whisper) and Word output (python-docx)
- `run.sh`: launcher that uses `.venv`
- `requirements.txt`: dependencies

## Troubleshooting

- **`ModuleNotFoundError: No module named 'PySide6'`**: the dependencies aren't installed in `.venv`. Rerun the setup steps.
- **`Failed to build 'av'`**: the venv is on Python 3.14 or newer. Recreate it with `uv venv -p 3.13 --clear .venv`.
- **`qt.qpa.wayland.textinput ...` warnings**: harmless. You can ignore them.
