from pathlib import Path

from platformdirs import user_data_dir, user_log_dir
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.credentials import load_secret


def _env_files() -> tuple[str, ...]:
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
    ]
    found = []
    for path in candidates:
        if path.is_file() and str(path) not in found:
            found.append(str(path))
    return tuple(found) or (".env",)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_files(), extra="ignore")
    app_name: str = "Community Pulse AI"
    openai_api_key: str | None = None
    community_pulse_model: str = "gpt-4.1-mini"
    tavily_api_key: str | None = None
    brave_api_key: str | None = None
    serper_api_key: str | None = None
    google_cse_api_key: str | None = None
    google_cse_id: str | None = None
    request_timeout: float = 15.0

    @model_validator(mode="after")
    def fill_from_keyring(self):
        self.openai_api_key = load_secret("OPENAI_API_KEY", self.openai_api_key)
        self.tavily_api_key = load_secret("TAVILY_API_KEY", self.tavily_api_key)
        self.brave_api_key = load_secret("BRAVE_API_KEY", self.brave_api_key)
        self.serper_api_key = load_secret("SERPER_API_KEY", self.serper_api_key)
        self.google_cse_api_key = load_secret("GOOGLE_CSE_API_KEY", self.google_cse_api_key)
        self.google_cse_id = load_secret("GOOGLE_CSE_ID", self.google_cse_id)
        return self

    @property
    def data_dir(self) -> Path:
        path = Path(user_data_dir("CommunityPulseAI", "Community Pulse"))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_dir(self) -> Path:
        path = Path(user_log_dir("CommunityPulseAI", "Community Pulse"))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'community_pulse.db'}"
