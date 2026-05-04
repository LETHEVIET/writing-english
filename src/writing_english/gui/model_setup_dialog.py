from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QProgressDialog,
    QMessageBox,
    QFileDialog,
    QWidget,
)

from writing_english.app.constants import GECTOR_ONNX_DIR
from writing_english.config.settings import Settings


class _DownloadThread(QThread):
    progress = Signal(int, str)
    finished_success = Signal(str)
    finished_error = Signal(str)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self.progress.emit(10, "Creating directories...")
            GECTOR_ONNX_DIR.mkdir(parents=True, exist_ok=True)

            self.progress.emit(30, "Downloading ONNX model from HuggingFace...")
            from huggingface_hub import snapshot_download

            snapshot_download(  # type: ignore[call-overload]
                repo_id=self._settings.gector_model
                or "letheviet/gector-roberta-base-5k-onnx",
                local_dir=str(GECTOR_ONNX_DIR),
                local_dir_use_symlinks=False,
            )

            self.progress.emit(100, "Done")
            self.finished_success.emit(str(GECTOR_ONNX_DIR))

        except Exception as exc:
            self.finished_error.emit(str(exc))


class ModelSetupDialog(QDialog):
    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Set Up Grammar Check")
        self.setMinimumWidth(360)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        desc = QLabel(
            "Grammar check requires a GECToR ONNX model.\n"
            "Choose how to provide the model files:"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._download_btn = QPushButton("Download model")
        self._download_btn.setToolTip(
            "Download the ONNX model from HuggingFace Hub (~520 MB)"
        )
        self._download_btn.clicked.connect(self._on_download)
        layout.addWidget(self._download_btn)

        self._load_btn = QPushButton("Load ONNX model from folder")
        self._load_btn.setToolTip("Point to an existing ONNX model directory")
        self._load_btn.clicked.connect(self._on_load)
        layout.addWidget(self._load_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self._cancel_btn)

    def _on_download(self) -> None:
        self._download_btn.setEnabled(False)
        self._load_btn.setEnabled(False)

        progress = QProgressDialog("Downloading model...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        self._thread = _DownloadThread(self._settings)

        def _update_progress(value: int, msg: str) -> None:
            progress.setValue(value)
            progress.setLabelText(msg)

        self._thread.progress.connect(_update_progress)
        self._thread.finished_success.connect(
            lambda path: self._on_download_finished(path, None)
        )
        self._thread.finished_error.connect(
            lambda msg: self._on_download_finished(None, msg)
        )
        progress.canceled.connect(self._thread.cancel)
        self._thread.start()

    def _on_download_finished(self, path: str | None, error: str | None) -> None:
        if error:
            QMessageBox.warning(self, "Download Failed", str(error))
            self._download_btn.setEnabled(True)
            self._load_btn.setEnabled(True)
            return

        if path is not None:
            self._settings.gector_model_dir = path
            self._settings.sync()

        self.accept()

    def _on_load(self) -> None:
        path_str = QFileDialog.getExistingDirectory(self, "Select ONNX Model Folder")
        if not path_str:
            return

        path = Path(path_str)
        required = (
            "model.onnx",
            "config.json",
            "tokenizer.json",
            "verb-form-vocab.txt",
        )
        missing = [f for f in required if not (path / f).exists()]
        if missing:
            QMessageBox.warning(
                self,
                "Invalid Model Folder",
                "Missing required files:\n" + "\n".join(missing),
            )
            return

        self._settings.gector_model_dir = path_str
        self._settings.sync()
        self.accept()
