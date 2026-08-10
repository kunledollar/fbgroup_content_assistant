import logging
import sys
import traceback

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy.orm import Session

from app.config.settings import AppSettings
from app.database.bootstrap import initialize
from app.database.session import make_engine

APP_BUILD = "2026-08-11-buttons"


def _install_excepthook():
    def hook(exc_type, exc, tb):
        details = "".join(traceback.format_exception(exc_type, exc, tb))
        logging.error("Unhandled error:\n%s", details)
        try:
            QMessageBox.critical(
                None,
                "Community Pulse AI error",
                f"{exc_type.__name__}: {exc}\n\nDetails were saved to the log.",
            )
        except Exception:
            logging.debug("Could not show error dialog", exc_info=True)

    sys.excepthook = hook


def main():
    _install_excepthook()
    settings = AppSettings()
    logging.basicConfig(
        filename=settings.log_dir / "community_pulse.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info(
        "Starting %s build=%s tavily=%s openai=%s python=%s",
        settings.app_name,
        APP_BUILD,
        bool(settings.tavily_api_key),
        bool(settings.openai_api_key),
        sys.version.split()[0],
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Community Pulse AI")
    app.setFont(QFont("Segoe UI", 10))
    try:
        engine = make_engine(settings.database_url)
        initialize(engine)
        session = Session(engine)
        from app.ui.windows.main_window import MainWindow

        window = MainWindow(session, settings, build=APP_BUILD)
        window.show()
        code = app.exec()
        session.close()
        return code
    except Exception:
        logging.exception("Application startup failed")
        QMessageBox.critical(
            None,
            "Community Pulse AI",
            "The application could not start. Technical details were saved to the log.",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
