"""Desktop app: pick a recording, get a Word transcript."""

import sys
from pathlib import Path

from PySide6.QtCore import QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

import transcriber

AUDIO_FILTER = "Audio/Video (*.mp3 *.wav *.m4a *.flac *.ogg *.opus *.aac *.wma *.mp4 *.mkv *.mov *.webm);;All files (*)"
# Plain-language names for the Whisper models; the real name is what gets loaded.
MODEL_CHOICES = {
    "Fastest (lower accuracy)": "base",
    "Balanced (recommended)": "small",
    "Most accurate (slow)": "medium",
}
LANGUAGES = {"Auto-detect": None, "English": "en", "Spanish": "es", "French": "fr", "German": "de",
             "Portuguese": "pt", "Italian": "it", "Dutch": "nl", "Hindi": "hi", "Chinese": "zh",
             "Japanese": "ja", "Arabic": "ar"}


def friendly_error(e):
    """Turn a technical exception into a sentence a non-technical user can act on."""
    text = f"{type(e).__name__}: {e}"
    lowered = text.lower()
    if any(k in lowered for k in ("connection", "network", "resolve", "timed out", "huggingface", "offline")):
        return ("Couldn't download the speech model. Check your internet connection and try again "
                "(this is only needed the first time).")
    if any(k in lowered for k in ("invaliddata", "invalid data", "no such stream", "averror", "decod")):
        return "This file couldn't be read. Make sure it is an audio or video recording."
    if isinstance(e, PermissionError):
        return "Couldn't save the Word document there. Close it if it's open in Word, or choose another folder."
    if isinstance(e, MemoryError):
        return "Your computer ran out of memory. Try the \"Fastest\" quality setting."
    return f"Something went wrong.\n\nDetails: {text}"


class Worker(QThread):
    status = Signal(str)
    progress = Signal(int)
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, audio, output, model, language, timestamps):
        super().__init__()
        self.audio, self.output = audio, output
        self.model, self.language, self.timestamps = model, language, timestamps
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        try:
            segments, info = transcriber.transcribe(
                self.audio, self.model, self.language,
                self.status.emit, self.progress.emit, lambda: self._cancel,
            )
            if not segments:
                self.failed.emit("No speech was detected in this recording.")
                return
            self.status.emit("Writing Word document...")
            transcriber.write_docx(segments, self.audio, self.output, self.timestamps,
                                   info.language, info.duration)
            self.done.emit(self.output)
        except InterruptedError:
            self.failed.emit("Cancelled.")
        except Exception as e:  # surface any model/ffmpeg/IO error in the UI
            self.failed.emit(friendly_error(e))


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Recording to Word")
        self.setMinimumWidth(480)
        self.setAcceptDrops(True)
        self.audio = None
        self.worker = None

        self.file_label = QLabel("Drop a recording here, or click Choose file")
        self.file_label.setWordWrap(True)
        choose = QPushButton("Choose file...")
        choose.clicked.connect(self.choose_file)

        self.model = QComboBox()
        self.model.addItems(MODEL_CHOICES)
        self.model.setCurrentText("Balanced (recommended)")
        self.model.setToolTip("More accurate settings take longer")
        self.language = QComboBox()
        self.language.addItems(LANGUAGES)
        self.timestamps = QCheckBox("Include timestamps")
        self.timestamps.setChecked(True)

        opts = QHBoxLayout()
        opts.addWidget(QLabel("Quality:"))
        opts.addWidget(self.model)
        opts.addWidget(QLabel("Language:"))
        opts.addWidget(self.language)

        self.start = QPushButton("Generate Word document")
        self.start.setEnabled(False)
        self.start.clicked.connect(self.begin)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(lambda: self.worker and self.worker.cancel())
        buttons = QHBoxLayout()
        buttons.addWidget(self.start)
        buttons.addWidget(self.cancel_btn)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.status = QLabel("")

        layout = QVBoxLayout(self)
        for w in (self.file_label, choose):
            layout.addWidget(w)
        layout.addLayout(opts)
        layout.addWidget(self.timestamps)
        layout.addLayout(buttons)
        layout.addWidget(self.bar)
        layout.addWidget(self.status)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            self.set_file(urls[0].toLocalFile())

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose a recording", str(Path.home()), AUDIO_FILTER)
        if path:
            self.set_file(path)

    def set_file(self, path):
        self.audio = path
        self.file_label.setText(path)
        self.start.setEnabled(True)
        self.bar.setValue(0)
        self.status.setText("")

    def begin(self):
        default = str(Path(self.audio).with_suffix(".docx"))
        output, _ = QFileDialog.getSaveFileName(self, "Save Word document", default, "Word document (*.docx)")
        if not output:
            return
        if not output.lower().endswith(".docx"):
            output += ".docx"
        self.set_busy(True)
        self.worker = Worker(self.audio, output, MODEL_CHOICES[self.model.currentText()],
                             LANGUAGES[self.language.currentText()], self.timestamps.isChecked())
        self.worker.status.connect(self.status.setText)
        self.worker.progress.connect(self.bar.setValue)
        self.worker.done.connect(self.finished_ok)
        self.worker.failed.connect(self.finished_err)
        self.worker.start()

    def set_busy(self, busy):
        self.start.setEnabled(not busy and self.audio is not None)
        self.cancel_btn.setEnabled(busy)

    def finished_ok(self, path):
        self.set_busy(False)
        self.status.setText(f"Saved: {path}")
        box = QMessageBox(self)
        box.setWindowTitle("Done")
        box.setText(f"Your Word document is ready:\n{path}")
        open_btn = box.addButton("Open document", QMessageBox.AcceptRole)
        folder_btn = box.addButton("Show in folder", QMessageBox.ActionRole)
        box.addButton("Close", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is open_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif box.clickedButton() is folder_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))

    def finished_err(self, msg):
        self.set_busy(False)
        self.status.setText(msg)
        if msg != "Cancelled.":
            QMessageBox.warning(self, "Couldn't transcribe", msg)

    def closeEvent(self, e):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec())
