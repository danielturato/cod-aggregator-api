from app.models.tournament_models import QueryStatus
from app.depenencies import get_db
from fastapi import Depends


async def scrape_cmg(tournament_q_model, db = Depends(get_db)):
    tournament_q_model["status"] = QueryStatus.failed
    update_res = \
        await db["tournaments"].update_one({"_id": tournament_q_model["_id"]}, {"$set": tournament_q_model})
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
