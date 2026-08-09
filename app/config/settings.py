from pathlib import Path
from platformdirs import user_data_dir, user_log_dir
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Community Pulse AI"
    openai_api_key: str | None = None
    community_pulse_model: str = "gpt-4.1-mini"
    tavily_api_key: str | None = None
    brave_api_key: str | None = None
    serper_api_key: str | None = None
    google_cse_api_key: str | None = None
    google_cse_id: str | None = None
    request_timeout: float = 15.0

    @property
    def data_dir(self) -> Path:
        path = Path(user_data_dir("CommunityPulseAI", "Community Pulse")); path.mkdir(parents=True, exist_ok=True); return path
    @property
    def log_dir(self) -> Path:
        path = Path(user_log_dir("CommunityPulseAI", "Community Pulse")); path.mkdir(parents=True, exist_ok=True); return path
    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'community_pulse.db'}"
