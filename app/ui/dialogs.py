from PySide6.QtWidgets import QDialog,QDialogButtonBox,QFormLayout,QLineEdit,QComboBox
from app.models.entities import CommunityGroup,GroupTopic
class GroupDialog(QDialog):
    def __init__(self,parent=None,group=None):
        super().__init__(parent); self.setWindowTitle("Community profile"); f=QFormLayout(self)
        self.name=QLineEdit(group.name if group else ""); self.city=QLineEdit(group.city if group else ""); self.county=QLineEdit(group.county if group else "Essex County"); self.state=QLineEdit(group.state if group else "New Jersey")
        self.topics=QLineEdit(", ".join(x.name for x in group.topics) if group else ""); self.excluded=QLineEdit(group.excluded_keywords if group else "")
        self.tone=QComboBox(); self.tone.addItems(["Community","Professional","Newsroom","Conversational","Urgent"])
        for label,w in [("Name",self.name),("City",self.city),("County",self.county),("State",self.state),("Topics",self.topics),("Excluded keywords",self.excluded),("Tone",self.tone)]:f.addRow(label,w)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);f.addRow(buttons)
    def build(self,group=None):
        g=group or CommunityGroup(); g.name=self.name.text().strip();g.city=self.city.text().strip();g.county=self.county.text().strip();g.state=self.state.text().strip();g.excluded_keywords=self.excluded.text();g.tone=self.tone.currentText();g.topics=[GroupTopic(name=x.strip()) for x in self.topics.text().split(",") if x.strip()];return g
