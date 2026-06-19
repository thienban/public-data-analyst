from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./data.db"
    cache_ttl_hours: int = 24

    # French public API base URLs
    sirene_base_url: str = "https://recherche-entreprises.api.gouv.fr"
    datagouv_base_url: str = "https://www.data.gouv.fr/api/1"
    dvf_base_url: str = "https://api.cquest.org/dvf"

    class Config:
        env_file = ".env"


settings = Settings()
