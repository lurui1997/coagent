from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_chat_id: str = ""
    feishu_escalate_user_id: str = ""
    feishu_api_base: str = "https://open.feishu.cn/open-apis"
    demo_mode: bool = True
    mock_llm: bool = False
    database_path: str = "coagent.db"
    data_dir: Path = Path("data")

    tool_timeout_s: float = 3.0
    llm_timeout_s: float = 15.0
    feishu_timeout_s: float = 5.0
    pipeline_timeout_s: float = 30.0

    @property
    def use_mock_llm(self) -> bool:
        return self.mock_llm or not self.llm_api_key


settings = Settings()
