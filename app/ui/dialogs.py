from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
)

from app.models.entities import CommunityGroup, GroupTopic, Source


class GroupDialog(QDialog):
    def __init__(self, parent=None, group=None):
        super().__init__(parent)
        self.setWindowTitle("Community profile")
        form = QFormLayout(self)
        self.name = QLineEdit(group.name if group else "")
        self.city = QLineEdit(group.city if group else "")
        self.county = QLineEdit(group.county if group else "Essex County")
        self.state = QLineEdit(group.state if group else "New Jersey")
        self.topics = QLineEdit(", ".join(x.name for x in group.topics) if group else "")
        self.excluded = QLineEdit(group.excluded_keywords if group else "")
        self.facebook = QLineEdit(group.facebook_url if group and group.facebook_url else "")
        self.tone = QComboBox()
        self.tone.addItems(["Community", "Professional", "Newsroom", "Conversational", "Urgent"])
        if group and group.tone:
            idx = self.tone.findText(group.tone)
            if idx >= 0:
                self.tone.setCurrentIndex(idx)
        for label, widget in [
            ("Name", self.name),
            ("City", self.city),
            ("County", self.county),
            ("State", self.state),
            ("Topics", self.topics),
            ("Excluded keywords", self.excluded),
            ("Facebook group URL", self.facebook),
            ("Tone", self.tone),
        ]:
            form.addRow(label, widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def build(self, group=None):
        g = group or CommunityGroup()
        g.name = self.name.text().strip()
        g.city = self.city.text().strip()
        g.county = self.county.text().strip()
        g.state = self.state.text().strip()
        g.excluded_keywords = self.excluded.text()
        g.facebook_url = self.facebook.text().strip() or None
        g.tone = self.tone.currentText()
        g.topics = [GroupTopic(name=x.strip()) for x in self.topics.text().split(",") if x.strip()]
        return g


class SourceDialog(QDialog):
    def __init__(self, parent=None, source=None):
        super().__init__(parent)
        self.setWindowTitle("Trusted source")
        form = QFormLayout(self)
        self.name = QLineEdit(source.name if source else "")
        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(
            ["Government", "Schools", "Transportation", "Housing", "Public Safety", "Community", "News"]
        )
        if source:
            idx = self.category.findText(source.category)
            if idx >= 0:
                self.category.setCurrentIndex(idx)
            else:
                self.category.setEditText(source.category)
        self.website = QLineEdit(source.website_url if source else "")
        self.rss = QLineEdit(source.rss_url if source and source.rss_url else "")
        self.priority = QSpinBox()
        self.priority.setRange(1, 100)
        self.priority.setValue(source.priority if source else 50)
        self.enabled = QCheckBox("Enabled for discovery")
        self.enabled.setChecked(True if source is None else bool(source.enabled))
        for label, widget in [
            ("Name", self.name),
            ("Category", self.category),
            ("Website", self.website),
            ("RSS URL", self.rss),
            ("Priority", self.priority),
        ]:
            form.addRow(label, widget)
        form.addRow(self.enabled)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def build(self, source=None):
        s = source or Source()
        s.name = self.name.text().strip()
        s.category = self.category.currentText().strip() or "Community"
        s.website_url = self.website.text().strip()
        s.rss_url = self.rss.text().strip() or None
        s.priority = self.priority.value()
        s.enabled = self.enabled.isChecked()
        return s


class CustomRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom date range")
        form = QFormLayout(self)
        self.days = QSpinBox()
        self.days.setRange(1, 365)
        self.days.setValue(7)
        form.addRow("Look back (days)", self.days)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
