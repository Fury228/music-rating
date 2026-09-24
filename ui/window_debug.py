from __future__ import annotations

from pathlib import Path
from datetime import datetime

from PySide6.QtCore import QObject, QEvent, QTimer
from PySide6.QtWidgets import QApplication, QWidget


class WindowDebugTracker(QObject):
    """Diagnostics only: records unexpected top-level QWidget instances."""

    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self.log_path = Path.cwd() / "window_debug.log"
        self._last_snapshot = None
        self._armed_until = 0
        app.installEventFilter(self)
        self._write("\n=== Window debug started ===")
        self.snapshot("startup")

    def _write(self, text: str):
        stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        try:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(f"[{stamp}] {text}\n")
        except Exception:
            pass

    def _describe(self, widget: QWidget) -> str:
        geo = widget.geometry()
        parent = widget.parentWidget()
        title = widget.windowTitle().replace("\n", " ")
        obj = widget.objectName()
        flags = int(widget.windowFlags())
        return (
            f"{widget.__class__.__name__} obj={obj!r} title={title!r} "
            f"geo={geo.x()},{geo.y()},{geo.width()}x{geo.height()} "
            f"visible={widget.isVisible()} active={widget.isActiveWindow()} "
            f"parent={parent.__class__.__name__ if parent else None} flags=0x{flags:x}"
        )

    def snapshot(self, reason: str):
        widgets = [w for w in self.app.topLevelWidgets() if isinstance(w, QWidget)]
        lines = [f"TOPLEVEL SNAPSHOT: {reason}; count={len(widgets)}"]
        for w in widgets:
            lines.append("  " + self._describe(w))
        snapshot = "\n".join(lines)
        if snapshot != self._last_snapshot:
            self._write(snapshot)
            self._last_snapshot = snapshot

    def arm(self, reason: str):
        self._write(f"--- ARMED: {reason} ---")
        self.snapshot(reason + " / before")
        QTimer.singleShot(0, lambda: self.snapshot(reason + " / +0ms"))
        QTimer.singleShot(30, lambda: self.snapshot(reason + " / +30ms"))
        QTimer.singleShot(100, lambda: self.snapshot(reason + " / +100ms"))
        QTimer.singleShot(300, lambda: self.snapshot(reason + " / +300ms"))
        QTimer.singleShot(700, lambda: self.snapshot(reason + " / +700ms"))

    def eventFilter(self, watched, event):
        if isinstance(watched, QWidget):
            et = event.type()
            if et in (QEvent.Type.Show, QEvent.Type.ShowToParent, QEvent.Type.WindowActivate):
                if watched.isWindow() or watched.parentWidget() is None:
                    self._write("EVENT " + et.name + ": " + self._describe(watched))
                    self.snapshot("event " + et.name)
        return False
