# Recording to Word

A desktop app that turns an audio or video recording into a Word (`.docx`) transcript.
It uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and runs fully offline on the CPU once the model has been downloaded.

## Download (no setup needed)

Go to the [latest release](https://github.com/AaronVikta/speech-to-text/releases/latest) and download the file for your computer (ignore the "Source code" zips, they are for developers):

| Computer | File | How to open |
|---|---|---|
| Windows | `RecordingToWord-Windows-Setup.exe` | Double-click it and follow the installer. If Windows shows "Windows protected your PC", click **More info** → **Run anyway**. |
| Mac | `RecordingToWord-Mac.dmg` | Open it and drag **Recording to Word** into Applications. The first time, right-click the app → **Open** → **Open**. |
| Linux | `RecordingToWord-Linux.AppImage` | Right-click → Properties → allow running as a program, then double-click it. |

Then drop your recording onto the window, click **Generate Word document** and choose where to save it.
The first transcription downloads the speech model (a few hundred MB), so you need an internet connection that one time.

## Features

- Pick a file or drag and drop it: mp3, wav, m4a, flac, ogg, opus, aac, wma, mp4, mkv, mov or webm
- Quality choice: Fastest (`base` model), Balanced (`small`, the default) or Most accurate (`medium`)
- When it finishes, buttons open the document or its folder
- Detects the language automatically, or you can pick one
- Optional timestamps in the transcript
- Shows progress and lets you cancel

## Requirements (to run from source)

- Windows, macOS or Linux with a desktop
- **Python 3.13.** Use 3.13 or older, not 3.14 or newer: the pinned `av<17` has no prebuilt wheels for newer Pythons, and building it from source fails.
- [uv](https://docs.astral.sh/uv/) (recommended), to get the right Python without changing the system one

## Developer setup

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

## Building the downloads

Releases are built by GitHub Actions ([.github/workflows/release.yml](.github/workflows/release.yml)) on Windows, macOS and Linux:

```bash
git tag v1.0.0 && git push origin v1.0.0   # builds all three and publishes a GitHub Release
```

You can also start it from the Actions tab (**Build downloads** → **Run workflow**) to get the builds as artifacts without making a release.

To build locally (for your current OS only):

```bash
.venv/bin/python -m pip install pyinstaller
QT_QPA_PLATFORM=offscreen .venv/bin/python packaging/make_icons.py
.venv/bin/pyinstaller --noconfirm packaging/app.spec    # app folder in dist/RecordingToWord
packaging/build_appimage.sh                              # Linux only: dist/RecordingToWord-Linux.AppImage
```

## Files

- `app.py`: PySide6 GUI
- `transcriber.py`: transcription (faster-whisper) and Word output (python-docx)
- `run.sh`: launcher that uses `.venv`
- `requirements.txt`: dependencies
- `packaging/`: PyInstaller spec, icon generator, AppImage script, Windows installer (Inno Setup)

## Troubleshooting

- **`ModuleNotFoundError: No module named 'PySide6'`**: the dependencies aren't installed in `.venv`. Rerun the setup steps.
- **`Failed to build 'av'`**: the venv is on Python 3.14 or newer. Recreate it with `uv venv -p 3.13 --clear .venv`.
- **`qt.qpa.wayland.textinput ...` warnings**: harmless. You can ignore them.
