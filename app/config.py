from pydantic import BaseSettings


class Settings(BaseSettings):
    profile: str = "DEV"
    google_chrome_bin = "/app/.apt/opt/google/chrome/google-chrome"
    chromedriver_path = "/app/.chromedriver/bin/chromedriver"
    mongodb_url: str = "mongodb://root:password@localhost:27017"
    base_cmg_url: str = "https://www.checkmategaming.com"
    cmg_game_path: str = "/tournament/cross-platform/call-of-duty-vanguard"
    base_gb_url: str = "https://gamebattles.majorleaguegaming.com/tournaments"
    base_umg_url: str = "https://www.umggaming.com/g"
    umg_game_path: str = "/vanguard/tournaments"

    class Config:
        env_file = "process.env"
