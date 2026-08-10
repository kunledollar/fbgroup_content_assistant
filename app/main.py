import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy.orm import Session

from app.config.settings import AppSettings
from app.database.bootstrap import initialize
from app.database.session import make_engine


def main():
    settings=AppSettings();logging.basicConfig(filename=settings.log_dir/"community_pulse.log",level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s")
    app=QApplication(sys.argv);app.setApplicationName("Community Pulse AI")
    try:
        engine=make_engine(settings.database_url);initialize(engine);session=Session(engine)
        from app.ui.windows.main_window import MainWindow
        window=MainWindow(session,settings);window.show();code=app.exec();session.close();return code
    except Exception:
        logging.exception("Application startup failed");QMessageBox.critical(None,"Community Pulse AI","The application could not start. Technical details were saved to the log.");return 1
if __name__=="__main__":raise SystemExit(main())
