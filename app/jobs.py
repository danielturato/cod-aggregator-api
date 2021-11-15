import asyncio

from app.models.tournament_models import QueryStatus
import motor.motor_asyncio
from app.config import Settings


def scrape_cmg(session_id):
    loop = asyncio.get_event_loop()
    coro = test(session_id)
    loop.create_task(coro)


async def test(session_id):
    settings = Settings()
    print(settings.mongodb_url)
    db = (motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_url)).vanguard_api
    if (tournament := await db["tournaments"].find_one({"session_id": session_id})) is not None:
        tournament["status"] = QueryStatus.failed

        update_res = \
            await db["tournaments"].update_one({"_id": tournament["_id"]}, {"$set": tournament})

        print(f"{update_res.modified_count} - res")
    else:
        print("FAILED")
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
