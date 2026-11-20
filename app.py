"""Desktop app: pick a recording, get a Word transcript."""

import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

import transcriber

AUDIO_FILTER = "Audio/Video (*.mp3 *.wav *.m4a *.flac *.ogg *.opus *.aac *.wma *.mp4 *.mkv *.mov *.webm);;All files (*)"
LANGUAGES = {"Auto-detect": None, "English": "en", "Spanish": "es", "French": "fr", "German": "de",
             "Portuguese": "pt", "Italian": "it", "Dutch": "nl", "Hindi": "hi", "Chinese": "zh",
             "Japanese": "ja", "Arabic": "ar"}


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
            self.failed.emit(str(e))


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
        self.model.addItems(transcriber.MODELS)
        self.model.setCurrentText("small")
        self.model.setToolTip("Bigger models are more accurate but slower")
        self.language = QComboBox()
        self.language.addItems(LANGUAGES)
        self.timestamps = QCheckBox("Include timestamps")
        self.timestamps.setChecked(True)

        opts = QHBoxLayout()
        opts.addWidget(QLabel("Model:"))
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
        self.worker = Worker(self.audio, output, self.model.currentText(),
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
        QMessageBox.information(self, "Done", f"Word document saved to:\n{path}")

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
