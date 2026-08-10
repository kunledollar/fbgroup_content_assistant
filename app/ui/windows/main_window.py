import json
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.models.entities import GeneratedPost
from app.providers.images import ImageProvider
from app.providers.llm import build_writer
from app.providers.search.factory import configured_provider
from app.repositories.core import GroupRepository, PostRepository, SourceRepository, StoryRepository
from app.services.writer import SafePostWriter
from app.ui.dialogs import CustomRangeDialog, GroupDialog, SourceDialog
from app.ui.workers import ResearchWorker
from app.utils.dates import RANGE_LABELS, since_for_range
from app.utils.topics import classify_topic

NAV = [
    "Dashboard",
    "Create Post",
    "Latest Stories",
    "Events",
    "Government",
    "Politics & Elections",
    "Schools & Parents",
    "Transportation",
    "Housing",
    "Public Safety",
    "Community Activities",
    "Projects & Development",
    "Complaints & Civic Issues",
    "Saved Stories",
    "Post History",
    "Groups",
    "Sources",
    "Settings",
]

STORY_PAGES = {
    "Latest Stories",
    "Events",
    "Government",
    "Politics & Elections",
    "Schools & Parents",
    "Transportation",
    "Housing",
    "Public Safety",
    "Community Activities",
    "Projects & Development",
    "Complaints & Civic Issues",
    "Saved Stories",
}


class MainWindow(QMainWindow):
    def __init__(self, session, settings):
        super().__init__()
        self.s = session
        self.settings = settings
        self.groups = GroupRepository(session)
        self.posts = PostRepository(session)
        self.sources_repo = SourceRepository(session)
        self.stories = StoryRepository(session)
        self.writer = build_writer(settings)
        self.safe_writer = SafePostWriter()
        self.images = ImageProvider()
        self.worker = None
        self.discovery_results = []
        self.custom_days = 7
        self.mode = "paste"
        self._story_tables = {}

        self.setWindowTitle("Community Pulse AI — Local Community News & Facebook Content Agent")
        self.resize(1380, 850)
        root = QWidget()
        layout = QHBoxLayout(root)
        self.nav = QListWidget()
        self.nav.addItems(NAV)
        self.nav.setFixedWidth(245)
        self.stack = QStackedWidget()
        layout.addWidget(self.nav)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self.pages = {}
        for name in NAV:
            page = self._create_page(name)
            self.pages[name] = page
            self.stack.addWidget(page)
        self.nav.currentRowChanged.connect(self._on_nav)
        self.nav.setCurrentRow(0)
        self._style(False)
        self._set_mode("paste")

    def _on_nav(self, index: int):
        self.stack.setCurrentIndex(index)
        name = NAV[index]
        if name in STORY_PAGES:
            self._refresh_story_page(name)
        elif name == "Post History":
            self._refresh_history()
        elif name == "Sources":
            self._refresh_sources_table()
        elif name == "Groups":
            self._refresh_groups_table()
        elif name == "Settings":
            self._refresh_settings()

    def _create_page(self, name):
        if name == "Create Post":
            return self._create_post()
        if name == "Groups":
            return self._groups_page()
        if name == "Sources":
            return self._sources_page()
        if name == "Post History":
            return self._history_page()
        if name in STORY_PAGES:
            return self._story_library_page(name)

        w = QWidget()
        v = QVBoxLayout(w)
        title = QLabel(name)
        title.setObjectName("pageTitle")
        v.addWidget(title)
        if name == "Dashboard":
            v.addWidget(
                QLabel(
                    "Your local newsroom research desk\n\n"
                    "Select Create Post to discover, verify, rank, and draft community updates.\n"
                    "Manage editable communities, trusted sources, drafts, and publishing history locally."
                )
            )
            b = QPushButton("Create a community post")
            b.clicked.connect(lambda: self.nav.setCurrentRow(NAV.index("Create Post")))
            v.addWidget(b)
        elif name == "Settings":
            self.settings_label = QLabel()
            self.settings_label.setWordWrap(True)
            v.addWidget(self.settings_label)
            self._refresh_settings()
            theme = QPushButton("Toggle light / dark mode")
            theme.setCheckable(True)
            theme.toggled.connect(self._style)
            v.addWidget(theme)
        v.addStretch()
        return w

    def _refresh_settings(self):
        if not hasattr(self, "settings_label"):
            return
        _, provider_name = configured_provider(
            self.settings, self.sources_repo.enabled_rss_urls()
        )
        search_state = provider_name or "Not configured — paste drafting remains available"
        ai_state = (
            "Configured"
            if self.settings.openai_api_key
            else "Not configured — local safe writer remains available"
        )
        self.settings_label.setText(
            f"Search provider: {search_state}\n"
            f"AI provider: OpenAI ({ai_state})\n"
            f"Model: {self.settings.community_pulse_model}\n"
            "Credentials are loaded from the environment (.env) or OS credential storage."
        )

    def _create_post(self):
        w = QWidget()
        v = QVBoxLayout(w)
        h = QLabel("Which community are you posting to?")
        h.setObjectName("pageTitle")
        v.addWidget(h)

        top = QHBoxLayout()
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)
        self._reload_groups()
        top.addWidget(self.group_combo, 1)
        add = QPushButton("+ Add Community")
        add.clicked.connect(self._add_group)
        top.addWidget(add)
        open_fb = QPushButton("Open Facebook group")
        open_fb.clicked.connect(self._open_facebook)
        top.addWidget(open_fb)
        v.addLayout(top)

        modes = QHBoxLayout()
        self.btn_discover = QPushButton("Discover Latest Stories")
        self.btn_search = QPushButton("Search a Topic")
        self.btn_paste = QPushButton("Paste Information")
        self.btn_discover.clicked.connect(self._click_discover)
        self.btn_search.clicked.connect(self._click_search)
        self.btn_paste.clicked.connect(self._click_paste)
        for btn in (self.btn_discover, self.btn_search, self.btn_paste):
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            modes.addWidget(btn)
        v.addLayout(modes)

        filters = QHBoxLayout()
        self.topic = QLineEdit()
        self.topic.setPlaceholderText("Topic, URL, or resident-supplied context")
        self.range = QComboBox()
        self.range.addItems(RANGE_LABELS)
        self.range.setCurrentText("Last 7 Days")
        filters.addWidget(self.topic, 1)
        filters.addWidget(self.range)
        self.run_btn = QPushButton("Run discovery")
        self.run_btn.clicked.connect(self._run_discovery)
        filters.addWidget(self.run_btn)
        v.addLayout(filters)

        self.status_note = QLabel(
            "Select a community, then click Discover Latest Stories to search online. "
            "Or click Paste Information to draft from text you already have."
        )
        self.status_note.setWordWrap(True)
        v.addWidget(self.status_note)

        split = QSplitter()
        left = QWidget()
        lv = QVBoxLayout(left)
        self.left_title = QLabel("PASTE INFORMATION / NOTES")
        lv.addWidget(self.left_title)

        self.input = QTextEdit()
        self.input.setPlaceholderText(
            "Paste an announcement, article, URL, meeting notice, complaint, or resident information…"
        )
        lv.addWidget(self.input)

        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self._on_result_selected)
        self.results_list.hide()
        lv.addWidget(self.results_list)

        self.create_btn = QPushButton("Create responsible draft")
        self.create_btn.clicked.connect(self._draft_from_paste)
        lv.addWidget(self.create_btn)

        self.use_story_btn = QPushButton("Generate draft from selected story")
        self.use_story_btn.clicked.connect(self._draft_from_selected)
        self.use_story_btn.hide()
        lv.addWidget(self.use_story_btn)

        self.save_story_btn = QPushButton("Save selected story")
        self.save_story_btn.clicked.connect(self._save_selected_story)
        self.save_story_btn.hide()
        lv.addWidget(self.save_story_btn)

        self.rank_label = QLabel("")
        self.rank_label.setWordWrap(True)
        lv.addWidget(self.rank_label)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.addWidget(QLabel("HEADLINE"))
        self.headline = QLineEdit()
        rv.addWidget(self.headline)
        toolbar = QToolBar()
        for label, fn in [
            ("Undo", lambda: self.editor.undo()),
            ("Redo", lambda: self.editor.redo()),
            ("Copy", self._copy),
            ("Save Draft", self._save_draft),
        ]:
            toolbar.addAction(label).triggered.connect(fn)
        rv.addWidget(toolbar)
        self.editor = QTextEdit()
        rv.addWidget(self.editor)
        rv.addWidget(QLabel("SOURCES (always retained separately)"))
        self.sources = QTextEdit()
        self.sources.setMaximumHeight(110)
        self.sources.setPlaceholderText("One verified source per line: publisher | title | date | URL")
        rv.addWidget(self.sources)
        rv.addWidget(QLabel("IMAGE GUIDANCE"))
        self.image_note = QLabel("No image selected. Copyrighted news photographs are never downloaded.")
        self.image_note.setWordWrap(True)
        rv.addWidget(self.image_note)

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([520, 760])
        v.addWidget(split, 1)
        return w

    def _click_discover(self):
        self._set_mode("discover")
        self.statusBar().showMessage("Searching online for latest community stories…", 4000)
        self._run_discovery()

    def _click_search(self):
        self._set_mode("search")
        if not self.topic.text().strip():
            self.topic.setFocus()
            self.status_note.setText("Type a topic above (example: housing, schools, NJ Transit), then click Search a Topic again.")
            self.statusBar().showMessage("Enter a topic to search", 4000)
            QMessageBox.information(
                self,
                "Enter a topic",
                "Type what you want to research in the topic box, then click Search a Topic again.",
            )
            return
        self.statusBar().showMessage(f"Searching online for: {self.topic.text().strip()}", 4000)
        self._run_discovery()

    def _click_paste(self):
        self._set_mode("paste")
        self.input.setFocus()
        self.statusBar().showMessage("Paste mode — add notes on the left, then Create responsible draft", 4000)

    def _set_mode(self, mode: str):
        self.mode = mode
        discovering = mode in {"discover", "search"}
        self.btn_discover.setChecked(mode == "discover")
        self.btn_search.setChecked(mode == "search")
        self.btn_paste.setChecked(mode == "paste")
        self.input.setVisible(not discovering)
        self.create_btn.setVisible(not discovering)
        self.results_list.setVisible(discovering)
        self.use_story_btn.setVisible(discovering)
        self.save_story_btn.setVisible(discovering)
        self.run_btn.setVisible(discovering)
        if mode == "discover":
            self.left_title.setText("DISCOVERED / RANKED STORIES")
            self.status_note.setText(
                "Searching with your community topics via Tavily/RSS. Results appear in the left list."
            )
            if not self.topic.text().strip():
                self.topic.setPlaceholderText("Optional focus topic (uses community topics if empty)")
        elif mode == "search":
            self.left_title.setText("SEARCH RESULTS")
            self.status_note.setText("Search mode — enter a topic, then click Search a Topic to run.")
            self.topic.setPlaceholderText("Required: topic to research")
        else:
            self.left_title.setText("PASTE INFORMATION / NOTES")
            self.status_note.setText(
                "Paste mode — put source material on the left, then click Create responsible draft. "
                "Claims stay marked unverified until you add sources."
            )
            self.topic.setPlaceholderText("Topic, URL, or resident-supplied context")
            self.rank_label.setText("")

    def _current_group(self):
        groups = self.groups.all()
        if not groups:
            return None
        idx = self.group_combo.currentIndex()
        return groups[idx] if 0 <= idx < len(groups) else groups[0]

    def _resolve_since(self):
        label = self.range.currentText()
        if label == "Custom Date Range":
            dialog = CustomRangeDialog(self)
            if dialog.exec():
                self.custom_days = dialog.days.value()
            return since_for_range(label, self.custom_days)
        return since_for_range(label)

    def _run_discovery(self):
        group = self._current_group()
        if not group:
            return QMessageBox.information(self, "Community required", "Add or select a community first.")
        topic = self.topic.text().strip()
        if self.mode == "search" and not topic:
            return QMessageBox.information(self, "Topic required", "Enter a topic to search.")
        provider, name = configured_provider(self.settings, self.sources_repo.enabled_rss_urls())
        if not provider:
            return QMessageBox.information(
                self,
                "Discovery unavailable",
                "Configure Tavily, Brave, Serper, Google CSE, or add RSS URLs under Sources.",
            )
        if self.worker and self.worker.isRunning():
            return QMessageBox.information(self, "Busy", "Discovery is already running.")
        since = self._resolve_since()
        self.results_list.clear()
        self.discovery_results = []
        self.rank_label.setText("")
        self.status_note.setText(f"Running discovery with {name}…")
        self.run_btn.setEnabled(False)
        self.worker = ResearchWorker(provider, group, since, topic, self)
        self.worker.completed.connect(self._on_discovery_done)
        self.worker.failed.connect(self._on_discovery_failed)
        self.worker.finished.connect(lambda: self.run_btn.setEnabled(True))
        self.worker.start()

    def _on_discovery_done(self, ranked):
        self.discovery_results = ranked or []
        self.results_list.clear()
        if not self.discovery_results:
            self.status_note.setText("No locally relevant stories found for this window. Try another topic or range.")
            return
        group = self._current_group()
        for score, reason, item in self.discovery_results:
            topic = classify_topic(item.title, item.summary, fallback="Community")
            self.stories.upsert_from_result(item, score, reason, topic=topic)
            row = QListWidgetItem(f"{score:.0f} · {item.title}")
            row.setData(Qt.UserRole, reason)
            self.results_list.addItem(row)
        self.status_note.setText(
            f"Found {len(self.discovery_results)} ranked stories for {group.name if group else 'community'}. "
            "Select one to review ranking, then generate a draft."
        )
        self._refresh_all_story_pages()

    def _on_discovery_failed(self, message: str):
        self.status_note.setText("Discovery failed. Check credentials, connectivity, and the application log.")
        QMessageBox.warning(self, "Discovery failed", message)

    def _on_result_selected(self):
        row = self.results_list.currentRow()
        if row < 0 or row >= len(self.discovery_results):
            self.rank_label.setText("")
            return
        score, reason, item = self.discovery_results[row]
        suggestion = self.images.suggest(item, self._current_group())
        self.rank_label.setText(
            f"Score {score:.1f}/100 — {reason}\n"
            f"Source: {item.source} · Confidence signal: {item.reliability:.0%}\n"
            f"{item.summary[:280]}"
        )
        self.image_note.setText(
            f"{suggestion.title}\nLicense: {suggestion.license}\n"
            f"Attribution: {suggestion.attribution or '—'}\n{suggestion.note}"
        )

    def _selected_result(self):
        row = self.results_list.currentRow()
        if row < 0 or row >= len(self.discovery_results):
            return None
        return self.discovery_results[row]

    def _draft_from_selected(self):
        selected = self._selected_result()
        if not selected:
            return QMessageBox.information(self, "Select a story", "Choose a ranked story first.")
        _, _, item = selected
        group = self._current_group()
        draft = self.writer.generate(item, group)
        self.headline.setText(draft.headline)
        self.editor.setPlainText(draft.body)
        published = item.published_at.strftime("%Y-%m-%d") if item.published_at else "unknown date"
        self.sources.setPlainText(f"{item.source} | {item.title} | {published} | {item.url}")
        suggestion = self.images.suggest(item, group)
        self.image_note.setText(
            f"{suggestion.title}\nLicense: {suggestion.license}\n"
            f"Attribution: {suggestion.attribution or '—'}\n{suggestion.note}"
        )
        if draft.warnings:
            self.statusBar().showMessage(draft.warnings[0], 5000)

    def _save_selected_story(self):
        selected = self._selected_result()
        if not selected:
            return QMessageBox.information(self, "Select a story", "Choose a ranked story first.")
        score, reason, item = selected
        topic = classify_topic(item.title, item.summary)
        story = self.stories.upsert_from_result(item, score, reason, topic=topic)
        self.stories.set_saved(story, True)
        self.statusBar().showMessage("Story saved to library", 3000)
        self._refresh_all_story_pages()

    def _draft_from_paste(self):
        text = self.input.toPlainText().strip()
        if not text:
            return QMessageBox.information(self, "Paste information", "Paste source material or notes first.")
        group = self._current_group()
        if not group:
            return QMessageBox.information(self, "Community required", "Add or select a community first.")
        draft = self.safe_writer.from_paste(text, group)
        self.headline.setText(draft.headline)
        self.editor.setPlainText(draft.body)
        self.sources.setPlainText("Resident / pasted information | local notes | unknown date | (no URL)")
        self.image_note.setText(
            "No automatic image selected.\n"
            "License: Not selected\n"
            "Copyrighted news images are never downloaded."
        )
        if draft.warnings:
            self.statusBar().showMessage(draft.warnings[0], 5000)

    def _copy(self):
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(self.editor.toPlainText())
        self.statusBar().showMessage("Post copied to clipboard", 3000)

    def _save_draft(self):
        if not self.editor.toPlainText().strip():
            return
        group = self._current_group()
        if not group:
            return
        self.posts.save(
            GeneratedPost(
                group_id=group.id,
                headline=self.headline.text() or "Untitled",
                body=self.editor.toPlainText(),
                sources_json=json.dumps(self.sources.toPlainText().splitlines()),
                status="Draft",
            )
        )
        self.statusBar().showMessage("Draft saved locally", 3000)
        self._refresh_history()

    def _open_facebook(self):
        group = self._current_group()
        if not group:
            return
        if group.facebook_url:
            webbrowser.open(group.facebook_url)
            return
        QMessageBox.information(
            self,
            "Facebook URL missing",
            "Edit this community profile and add the Facebook group URL, then open it manually after copying your post.",
        )

    def _groups_page(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Communities", objectName="pageTitle"))
        self.group_table = QTableWidget(0, 4)
        self.group_table.setHorizontalHeaderLabels(["Name", "City", "County", "Topics"])
        v.addWidget(self.group_table)
        buttons = QHBoxLayout()
        for label, fn in [("Add", self._add_group), ("Edit", self._edit_group), ("Delete", self._delete_group)]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            buttons.addWidget(b)
        v.addLayout(buttons)
        self._refresh_groups_table()
        return w

    def _add_group(self):
        d = GroupDialog(self)
        if d.exec():
            self.groups.add(d.build())
            self._reload_groups()
            self._refresh_groups_table()

    def _edit_group(self):
        row = self.group_table.currentRow()
        gs = self.groups.all()
        if row < 0:
            return
        d = GroupDialog(self, gs[row])
        if d.exec():
            d.build(gs[row])
            self.s.commit()
            self._reload_groups()
            self._refresh_groups_table()

    def _delete_group(self):
        row = self.group_table.currentRow()
        gs = self.groups.all()
        if row >= 0 and QMessageBox.question(
            self, "Delete community", "Delete this editable community profile?"
        ) == QMessageBox.Yes:
            self.groups.delete(gs[row])
            self._reload_groups()
            self._refresh_groups_table()

    def _reload_groups(self):
        if not hasattr(self, "group_combo"):
            return
        self.group_combo.clear()
        self.group_combo.addItems([x.name for x in self.groups.all()])

    def _refresh_groups_table(self):
        if not hasattr(self, "group_table"):
            return
        gs = self.groups.all()
        self.group_table.setRowCount(len(gs))
        for r, g in enumerate(gs):
            for c, val in enumerate((g.name, g.city, g.county, ", ".join(x.name for x in g.topics))):
                self.group_table.setItem(r, c, QTableWidgetItem(val))
        self.group_table.resizeColumnsToContents()

    def _sources_page(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Trusted Sources", objectName="pageTitle"))
        v.addWidget(
            QLabel(
                "Prioritized sources for verification. Add RSS feeds to enable offline discovery without an API key."
            )
        )
        self.source_table = QTableWidget(0, 5)
        self.source_table.setHorizontalHeaderLabels(["Source", "Category", "Priority", "Website", "RSS"])
        v.addWidget(self.source_table)
        buttons = QHBoxLayout()
        for label, fn in [
            ("Add", self._add_source),
            ("Edit", self._edit_source),
            ("Delete", self._delete_source),
            ("Open website", self._open_source_website),
        ]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            buttons.addWidget(b)
        v.addLayout(buttons)
        self._refresh_sources_table()
        return w

    def _refresh_sources_table(self):
        if not hasattr(self, "source_table"):
            return
        items = self.sources_repo.all()
        self.source_table.setRowCount(len(items))
        for r, x in enumerate(items):
            for c, val in enumerate(
                (x.name, x.category, str(x.priority), x.website_url, x.rss_url or "")
            ):
                self.source_table.setItem(r, c, QTableWidgetItem(val))
        self.source_table.resizeColumnsToContents()

    def _add_source(self):
        d = SourceDialog(self)
        if d.exec():
            source = d.build()
            if not source.name or not source.website_url:
                return QMessageBox.information(self, "Source incomplete", "Name and website are required.")
            self.sources_repo.add(source)
            self._refresh_sources_table()

    def _edit_source(self):
        row = self.source_table.currentRow()
        items = self.sources_repo.all()
        if row < 0:
            return
        d = SourceDialog(self, items[row])
        if d.exec():
            d.build(items[row])
            self.sources_repo.save()
            self._refresh_sources_table()

    def _delete_source(self):
        row = self.source_table.currentRow()
        items = self.sources_repo.all()
        if row >= 0 and QMessageBox.question(
            self, "Delete source", "Remove this trusted source?"
        ) == QMessageBox.Yes:
            self.sources_repo.delete(items[row])
            self._refresh_sources_table()

    def _open_source_website(self):
        row = self.source_table.currentRow()
        items = self.sources_repo.all()
        if row >= 0 and items[row].website_url:
            webbrowser.open(items[row].website_url)

    def _history_page(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Post History", objectName="pageTitle"))
        self.history = QTableWidget(0, 4)
        self.history.setHorizontalHeaderLabels(["Created", "Headline", "Status", "Community"])
        v.addWidget(self.history)
        buttons = QHBoxLayout()
        for label, fn in [
            ("Open in editor", self._open_history_draft),
            ("Copy", self._copy_history_draft),
            ("Delete", self._delete_history_draft),
        ]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            buttons.addWidget(b)
        v.addLayout(buttons)
        self._refresh_history()
        return w

    def _refresh_history(self):
        if not hasattr(self, "history"):
            return
        posts = self.posts.all()
        group_names = {g.id: g.name for g in self.groups.all()}
        self.history.setRowCount(len(posts))
        for r, x in enumerate(posts):
            vals = (
                x.created_at.strftime("%Y-%m-%d %H:%M"),
                x.headline,
                x.status,
                group_names.get(x.group_id, str(x.group_id)),
            )
            for c, val in enumerate(vals):
                self.history.setItem(r, c, QTableWidgetItem(val))
        self.history.resizeColumnsToContents()

    def _selected_history_post(self):
        row = self.history.currentRow()
        posts = self.posts.all()
        if row < 0 or row >= len(posts):
            return None
        return posts[row]

    def _open_history_draft(self):
        post = self._selected_history_post()
        if not post:
            return
        self.nav.setCurrentRow(NAV.index("Create Post"))
        self.headline.setText(post.headline)
        self.editor.setPlainText(post.body)
        try:
            lines = json.loads(post.sources_json or "[]")
            self.sources.setPlainText("\n".join(lines) if isinstance(lines, list) else str(lines))
        except json.JSONDecodeError:
            self.sources.setPlainText(post.sources_json or "")
        groups = self.groups.all()
        for i, g in enumerate(groups):
            if g.id == post.group_id:
                self.group_combo.setCurrentIndex(i)
                break
        self.statusBar().showMessage("Draft loaded into Create Post", 3000)

    def _copy_history_draft(self):
        from PySide6.QtWidgets import QApplication

        post = self._selected_history_post()
        if not post:
            return
        QApplication.clipboard().setText(post.body)
        self.statusBar().showMessage("Historical post copied", 3000)

    def _delete_history_draft(self):
        post = self._selected_history_post()
        if not post:
            return
        if QMessageBox.question(self, "Delete draft", "Delete this saved draft?") == QMessageBox.Yes:
            self.posts.delete(post)
            self._refresh_history()

    def _story_library_page(self, name: str):
        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel(name, objectName="pageTitle"))
        v.addWidget(
            QLabel(
                "Stories discovered and ranked from Create Post appear here after research runs. "
                "Select a row, then open it in the post studio."
            )
        )
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["Score", "Title", "Source", "Topic", "Confidence"])
        v.addWidget(table)
        buttons = QHBoxLayout()
        open_btn = QPushButton("Open in Create Post")
        save_btn = QPushButton("Toggle saved")
        open_btn.clicked.connect(lambda: self._open_library_story(name))
        save_btn.clicked.connect(lambda: self._toggle_library_saved(name))
        buttons.addWidget(open_btn)
        buttons.addWidget(save_btn)
        v.addLayout(buttons)
        self._story_tables[name] = table
        self._refresh_story_page(name)
        return w

    def _stories_for_page(self, name: str):
        if name == "Latest Stories":
            return self.stories.all()
        if name == "Saved Stories":
            return self.stories.saved()
        return self.stories.by_topic(name)

    def _refresh_story_page(self, name: str):
        table = self._story_tables.get(name)
        if table is None:
            return
        items = self._stories_for_page(name)
        table.setRowCount(len(items))
        for r, story in enumerate(items):
            vals = (
                f"{story.score:.0f}",
                story.title,
                story.source_name,
                story.topic,
                story.confidence,
            )
            for c, val in enumerate(vals):
                table.setItem(r, c, QTableWidgetItem(val))
        table.resizeColumnsToContents()

    def _refresh_all_story_pages(self):
        for name in self._story_tables:
            self._refresh_story_page(name)

    def _selected_library_story(self, name: str):
        table = self._story_tables.get(name)
        if table is None:
            return None
        row = table.currentRow()
        items = self._stories_for_page(name)
        if row < 0 or row >= len(items):
            return None
        return items[row]

    def _open_library_story(self, name: str):
        story = self._selected_library_story(name)
        if not story:
            return
        from app.models.schemas import SearchResult

        group = self._current_group()
        if not group:
            return QMessageBox.information(self, "Community required", "Select a community in Create Post first.")
        item = SearchResult(
            title=story.title,
            url=story.url,
            summary=story.summary,
            source=story.source_name,
            published_at=story.published_at,
            event_at=story.event_at,
            location=story.location,
            topic=story.topic,
            reliability=0.9 if story.confidence == "Verified" else 0.45,
        )
        self.nav.setCurrentRow(NAV.index("Create Post"))
        self._set_mode("discover")
        draft = self.writer.generate(item, group)
        self.headline.setText(draft.headline)
        self.editor.setPlainText(draft.body)
        published = story.published_at.strftime("%Y-%m-%d") if story.published_at else "unknown date"
        self.sources.setPlainText(f"{story.source_name} | {story.title} | {published} | {story.url}")
        self.rank_label.setText(f"Score {story.score:.1f}/100 — {story.score_reason}")
        suggestion = self.images.suggest(item, group)
        self.image_note.setText(
            f"{suggestion.title}\nLicense: {suggestion.license}\n"
            f"Attribution: {suggestion.attribution or '—'}\n{suggestion.note}"
        )

    def _toggle_library_saved(self, name: str):
        story = self._selected_library_story(name)
        if not story:
            return
        self.stories.set_saved(story, not story.saved)
        self._refresh_all_story_pages()

    def _style(self, dark):
        bg = "#101827" if dark else "#f4f7fb"
        fg = "#eef2f7" if dark else "#182334"
        card = "#182438" if dark else "white"
        accent = "#18a999"
        self.setStyleSheet(
            f"QWidget{{background:{bg};color:{fg};font-size:14px}} "
            f"QListWidget,QTextEdit,QLineEdit,QComboBox,QTableWidget{{background:{card};border:1px solid #627086;border-radius:6px;padding:6px}} "
            f"QPushButton{{background:{accent};color:white;border:0;border-radius:6px;padding:9px 14px}} "
            f"QPushButton:hover{{background:#12877b}} "
            f"QPushButton:checked{{background:#0f6f66;border:2px solid {'#9fe1d8' if dark else '#0b4f48'}}} "
            f"#pageTitle{{font-size:25px;font-weight:700;padding:12px 0}} "
            f"QListWidget::item{{padding:8px}} "
            f"QListWidget::item:selected{{background:{accent};color:white}}"
        )
