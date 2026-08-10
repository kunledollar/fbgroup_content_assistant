import asyncio

from PySide6.QtCore import QThread, Signal

from app.agents.orchestrator import ResearchOrchestrator


class ResearchWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, provider, group, since, topic, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.group = group
        self.since = since
        self.topic = topic

    def run(self):
        try:
            results = asyncio.run(
                ResearchOrchestrator(self.provider).run(self.group, self.since, self.topic)
            )
            self.completed.emit(results)
        except Exception as exc:
            self.failed.emit(str(exc) or exc.__class__.__name__)
