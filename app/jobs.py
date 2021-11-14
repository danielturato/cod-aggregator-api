import requests
from app.config import Settings
from fastapi import HTTPException


async def scrape_cmg():
    print("here")
    # if (tournament := await db["tournaments"].find_one({"_id": _id})) is not None:
    #     print("here boss")
    #     params = {
    #         'access_key': '46de6899530e79d890a81385fd0f29eb',
    #         'url': settings.base_cmg_url + settings.cmg_game_path,
    #         'render_js': 1
    #     }
    #     res = requests.get('https://api.scrapestack.com/scrape', params)
    #     print(res.content)
    # else:
    #     raise HTTPException(status_code=422, detail="Invalid request")
