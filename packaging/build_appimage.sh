#!/bin/bash
# Turn dist/RecordingToWord (PyInstaller output) into a single double-clickable AppImage.
set -euo pipefail
cd "$(dirname "$0")/.."
APPDIR=build/AppDir
rm -rf "$APPDIR" && mkdir -p "$APPDIR/usr"
cp -r dist/RecordingToWord "$APPDIR/usr/bin"
cp packaging/icon.png "$APPDIR/recording-to-word.png"
cat > "$APPDIR/recording-to-word.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Recording to Word
Comment=Turn a recording into a Word transcript
Exec=RecordingToWord
Icon=recording-to-word
Categories=AudioVideo;Office;
DESK
cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/RecordingToWord" "$@"
RUN
chmod +x "$APPDIR/AppRun"
TOOL=build/appimagetool
[ -x "$TOOL" ] || { curl -fsSL -o "$TOOL" https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage; chmod +x "$TOOL"; }
ARCH=x86_64 "$TOOL" --appimage-extract-and-run "$APPDIR" dist/RecordingToWord-Linux.AppImage
