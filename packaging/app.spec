# PyInstaller spec: bundles Python, Qt, faster-whisper and PyAV into one app folder.
# Build from the repo root:  pyinstaller packaging/app.spec
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

APP_NAME = "Recording to Word"
ROOT = os.path.dirname(SPECPATH)

datas = collect_data_files("faster_whisper")          # Silero VAD model used by vad_filter
binaries = collect_dynamic_libs("ctranslate2") + collect_dynamic_libs("av")

a = Analysis(
    [os.path.join(ROOT, "app.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=["docx", "ctranslate2"],
    excludes=["tkinter", "matplotlib", "IPython", "torch"],
)
pyz = PYZ(a.pure)
icon = os.path.join(SPECPATH, "icon.ico") if sys.platform == "win32" else (os.path.join(SPECPATH, "icon.icns") if sys.platform == "darwin" else None)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="RecordingToWord",
    console=False,
    icon=icon,
)
coll = COLLECT(exe, a.binaries, a.datas, name="RecordingToWord")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=icon,
        bundle_identifier="io.github.recordingtoword",
        info_plist={"NSHighResolutionCapable": True, "LSMinimumSystemVersion": "11.0"},
    )
