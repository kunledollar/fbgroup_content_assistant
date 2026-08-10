import logging
import sys
import traceback

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy.orm import Session

from app.config.settings import AppSettings
from app.database.bootstrap import initialize
from app.database.session import make_engine

APP_BUILD = "2026-08-11-editor-fix"


def _install_excepthook():
    def hook(exc_type, exc, tb):
        details = "".join(traceback.format_exception(exc_type, exc, tb))
        print(details, file=sys.stderr)
        logging.error("Unhandled error:\n%s", details)
        try:
            QMessageBox.critical(
                None,
                "Community Pulse AI error",
                f"{exc_type.__name__}: {exc}\n\nDetails were also printed in the terminal.",
            )
        except Exception:
            logging.debug("Could not show error dialog", exc_info=True)

    sys.excepthook = hook


def main():
    _install_excepthook()
    try:
        settings = AppSettings()
    except Exception as exc:
        details = traceback.format_exc()
        print(details, file=sys.stderr)
        print(f"Failed to load settings/env: {exc}", file=sys.stderr)
        return 1

    log_path = settings.log_dir / "community_pulse.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.info(
        "Starting %s build=%s tavily=%s openai=%s python=%s log=%s",
        settings.app_name,
        APP_BUILD,
        bool(settings.tavily_api_key),
        bool(settings.openai_api_key),
        sys.version.split()[0],
        log_path,
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
    except Exception as exc:
        details = traceback.format_exc()
        logging.exception("Application startup failed")
        print(details, file=sys.stderr)
        print(f"LOG FILE: {log_path}", file=sys.stderr)
        QMessageBox.critical(
            None,
            "Community Pulse AI",
            f"Startup failed:\n\n{type(exc).__name__}: {exc}\n\n"
            f"Full details are in the terminal and:\n{log_path}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
