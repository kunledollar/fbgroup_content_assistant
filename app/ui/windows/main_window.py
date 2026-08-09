import json, webbrowser
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QListWidget,QStackedWidget,QLabel,QComboBox,QPushButton,QTextEdit,QLineEdit,QTableWidget,QTableWidgetItem,QMessageBox,QSplitter,QToolBar)
from app.models.entities import GeneratedPost
from app.repositories.core import GroupRepository,PostRepository,SourceRepository
from app.ui.dialogs import GroupDialog

NAV=["Dashboard","Create Post","Latest Stories","Events","Government","Politics & Elections","Schools & Parents","Transportation","Housing","Public Safety","Community Activities","Projects & Development","Complaints & Civic Issues","Saved Stories","Post History","Groups","Sources","Settings"]
class MainWindow(QMainWindow):
    def __init__(self,session,settings):
        super().__init__();self.s=session;self.settings=settings;self.groups=GroupRepository(session);self.posts=PostRepository(session)
        self.setWindowTitle("Community Pulse AI — Local Community News & Facebook Content Agent");self.resize(1380,850)
        root=QWidget();layout=QHBoxLayout(root);self.nav=QListWidget();self.nav.addItems(NAV);self.nav.setFixedWidth(245);self.stack=QStackedWidget();layout.addWidget(self.nav);layout.addWidget(self.stack,1);self.setCentralWidget(root)
        self.pages={};
        for name in NAV:
            page=self._create_page(name);self.pages[name]=page;self.stack.addWidget(page)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex);self.nav.setCurrentRow(0);self._style(False)
    def _create_page(self,name):
        if name=="Create Post":return self._create_post()
        if name=="Groups":return self._groups_page()
        if name=="Sources":return self._sources_page()
        if name=="Post History":return self._history_page()
        w=QWidget();v=QVBoxLayout(w);title=QLabel(name);title.setObjectName("pageTitle");v.addWidget(title)
        if name=="Dashboard":
            v.addWidget(QLabel("Your local newsroom research desk\n\nSelect Create Post to research or transform verified information.\nManage editable communities, trusted sources, drafts, and publishing history locally."))
            b=QPushButton("Create a community post");b.clicked.connect(lambda:self.nav.setCurrentRow(NAV.index("Create Post")));v.addWidget(b)
        elif name=="Settings":
            state="Configured" if self.settings.openai_api_key else "Not configured — local editing remains available"
            v.addWidget(QLabel(f"AI provider: OpenAI ({state})\nModel: {self.settings.community_pulse_model}\nCredentials are loaded from the environment or OS credential storage."));theme=QPushButton("Toggle light / dark mode");theme.setCheckable(True);theme.toggled.connect(self._style);v.addWidget(theme)
        else:v.addWidget(QLabel("This workspace uses the same verified story library and filters. Discover content from Create Post."))
        v.addStretch();return w
    def _create_post(self):
        w=QWidget();v=QVBoxLayout(w);h=QLabel("Which community are you posting to?");h.setObjectName("pageTitle");v.addWidget(h)
        top=QHBoxLayout();self.group_combo=QComboBox();self.group_combo.setEditable(True);self._reload_groups();top.addWidget(self.group_combo,1);add=QPushButton("+ Add Community");add.clicked.connect(self._add_group);top.addWidget(add);v.addLayout(top)
        modes=QHBoxLayout();
        for text in ("Discover Latest Stories","Search a Topic","Paste Information"):modes.addWidget(QPushButton(text))
        v.addLayout(modes);filters=QHBoxLayout();self.topic=QLineEdit();self.topic.setPlaceholderText("Topic, URL, or resident-supplied context");self.range=QComboBox();self.range.addItems(["Today","Last 24 Hours","Last 3 Days","Last 7 Days","Last 14 Days","Last 30 Days","Custom Date Range"]);filters.addWidget(self.topic,1);filters.addWidget(self.range);v.addLayout(filters)
        note=QLabel("Research requires a configured search provider. Pasted claims remain marked unverified until supported by sources.");note.setWordWrap(True);v.addWidget(note)
        split=QSplitter();left=QWidget();lv=QVBoxLayout(left);lv.addWidget(QLabel("PASTE INFORMATION / NOTES"));self.input=QTextEdit();self.input.setPlaceholderText("Paste an announcement, article, URL, meeting notice, complaint, or resident information…");lv.addWidget(self.input);create=QPushButton("Create responsible draft");create.clicked.connect(self._draft_from_paste);lv.addWidget(create)
        right=QWidget();rv=QVBoxLayout(right);rv.addWidget(QLabel("HEADLINE"));self.headline=QLineEdit();rv.addWidget(self.headline);toolbar=QToolBar();
        for label,fn in [("Undo",lambda:self.editor.undo()),("Redo",lambda:self.editor.redo()),("Copy",self._copy), ("Save Draft",self._save_draft)]:toolbar.addAction(label).triggered.connect(fn)
        rv.addWidget(toolbar);self.editor=QTextEdit();rv.addWidget(self.editor);rv.addWidget(QLabel("SOURCES (always retained separately)"));self.sources=QTextEdit();self.sources.setMaximumHeight(130);self.sources.setPlaceholderText("One verified source per line: publisher | title | date | URL");rv.addWidget(self.sources);split.addWidget(left);split.addWidget(right);v.addWidget(split,1);return w
    def _draft_from_paste(self):
        text=self.input.toPlainText().strip();
        if not text:return QMessageBox.information(self,"Paste information","Paste source material or notes first.")
        headline=text.splitlines()[0][:150];self.headline.setText(headline);self.editor.setPlainText(f"UNVERIFIED COMMUNITY REPORT\n\n📍 COMMUNITY QUESTION\n\n{headline}\n\nSeveral residents or sources have raised the following information:\n\n{text}\n\nThis information has not yet been independently verified. Please share firsthand details or an official source without identifying private individuals.\n\n💬 What have you observed, and which public agency should follow up?")
    def _copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.editor.toPlainText());self.statusBar().showMessage("Post copied to clipboard",3000)
    def _save_draft(self):
        if not self.editor.toPlainText().strip():return
        groups=self.groups.all();idx=self.group_combo.currentIndex();g=groups[idx] if 0<=idx<len(groups) else groups[0]
        self.posts.save(GeneratedPost(group_id=g.id,headline=self.headline.text() or "Untitled",body=self.editor.toPlainText(),sources_json=json.dumps(self.sources.toPlainText().splitlines()),status="Draft"));self.statusBar().showMessage("Draft saved locally",3000);self._refresh_history()
    def _groups_page(self):
        w=QWidget();v=QVBoxLayout(w);v.addWidget(QLabel("Communities",objectName="pageTitle"));self.group_table=QTableWidget(0,4);self.group_table.setHorizontalHeaderLabels(["Name","City","County","Topics"]);v.addWidget(self.group_table);buttons=QHBoxLayout();
        for label,fn in [("Add",self._add_group),("Edit",self._edit_group),("Delete",self._delete_group)]:b=QPushButton(label);b.clicked.connect(fn);buttons.addWidget(b)
        v.addLayout(buttons);self._refresh_groups_table();return w
    def _add_group(self):
        d=GroupDialog(self)
        if d.exec():self.groups.add(d.build());self._reload_groups();self._refresh_groups_table()
    def _edit_group(self):
        row=self.group_table.currentRow();gs=self.groups.all()
        if row<0:return
        d=GroupDialog(self,gs[row]);
        if d.exec():d.build(gs[row]);self.s.commit();self._reload_groups();self._refresh_groups_table()
    def _delete_group(self):
        row=self.group_table.currentRow();gs=self.groups.all()
        if row>=0 and QMessageBox.question(self,"Delete community","Delete this editable community profile?")==QMessageBox.Yes:self.groups.delete(gs[row]);self._reload_groups();self._refresh_groups_table()
    def _reload_groups(self):
        if not hasattr(self,"group_combo"):return
        self.group_combo.clear();self.group_combo.addItems([x.name for x in self.groups.all()])
    def _refresh_groups_table(self):
        if not hasattr(self,"group_table"):return
        gs=self.groups.all();self.group_table.setRowCount(len(gs))
        for r,g in enumerate(gs):
            for c,val in enumerate((g.name,g.city,g.county,", ".join(x.name for x in g.topics))):self.group_table.setItem(r,c,QTableWidgetItem(val))
        self.group_table.resizeColumnsToContents()
    def _sources_page(self):
        w=QWidget();v=QVBoxLayout(w);v.addWidget(QLabel("Trusted Sources",objectName="pageTitle"));t=QTableWidget(0,4);t.setHorizontalHeaderLabels(["Source","Category","Priority","Website"]);items=SourceRepository(self.s).all();t.setRowCount(len(items))
        for r,x in enumerate(items):
            for c,val in enumerate((x.name,x.category,str(x.priority),x.website_url)):t.setItem(r,c,QTableWidgetItem(val))
        t.resizeColumnsToContents();v.addWidget(t);return w
    def _history_page(self):
        w=QWidget();v=QVBoxLayout(w);v.addWidget(QLabel("Post History",objectName="pageTitle"));self.history=QTableWidget(0,4);self.history.setHorizontalHeaderLabels(["Created","Headline","Status","Community ID"]);v.addWidget(self.history);self._refresh_history();return w
    def _refresh_history(self):
        if not hasattr(self,"history"):return
        p=self.posts.all();self.history.setRowCount(len(p))
        for r,x in enumerate(p):
            for c,val in enumerate((x.created_at.strftime("%Y-%m-%d %H:%M"),x.headline,x.status,str(x.group_id))):self.history.setItem(r,c,QTableWidgetItem(val))
    def _style(self,dark):
        bg="#101827" if dark else "#f4f7fb";fg="#eef2f7" if dark else "#182334";card="#182438" if dark else "white";accent="#18a999"
        self.setStyleSheet(f"QWidget{{background:{bg};color:{fg};font-size:14px}} QListWidget,QTextEdit,QLineEdit,QComboBox,QTableWidget{{background:{card};border:1px solid #627086;border-radius:6px;padding:6px}} QPushButton{{background:{accent};color:white;border:0;border-radius:6px;padding:9px 14px}} QPushButton:hover{{background:#12877b}} #pageTitle{{font-size:25px;font-weight:700;padding:12px 0}} QListWidget::item{{padding:8px}} QListWidget::item:selected{{background:{accent};color:white}}")
