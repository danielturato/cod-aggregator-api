from pydantic import BaseSettings, RedisDsn


class Settings(BaseSettings):
    profile: str = "DEV"
    mongodb_url: str = "mongodb://root:password@localhost:27017"
    redistogo_url: RedisDsn = "redis://localhost:6379"
    base_cmg_url: str = "https://www.checkmategaming.com"
    cmg_game_path: str = "/tournament/cross-platform/call-of-duty-vanguard"
    base_gb_url: str = "https://gamebattles.majorleaguegaming.com/tournaments"
    base_umg_url: str = "https://www.umggaming.com/g"
    umg_game_path: str = "/vanguard/tournaments"

    class Config:
        env_file = "process.env"
