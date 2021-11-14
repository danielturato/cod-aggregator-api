from pydantic import BaseSettings


class Settings(BaseSettings):
    profile: str = "PROD"
    mongodb_url: str
    google_chrome_bin: str
    chromedriver_path: str
    base_cmg_url: str
    cmg_game_path: str
    base_gb_url: str
    base_umg_url: str
    umg_game_path: str

    class Config:
        env_file = ".env"
