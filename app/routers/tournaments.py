from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import conset
from rq import Queue
from secrets import token_urlsafe

from app.depenencies import get_settings, verify_session_cookie, get_db, get_q
from app import config
from app.jobs import scrape_cmg
from app.models.tournament_models import TournamentSite, Region, TeamSize, TournamentQModel, QueryStatus

router = APIRouter()


class TournamentQuery:
    def __init__(
            self,
            sites: conset(TournamentSite, min_items=1, max_items=3) = Query(...),
            regions: conset(Region, min_items=1, max_items=3) = Query(...),
            team_sizes: conset(TeamSize, min_items=1, max_items=4, ) = Query(...)
    ):
        self.sites = sites
        self.regions = regions
        self.team_sizes = team_sizes


@router.get("/tournaments", response_model=TournamentQModel)
async def get_tournaments(tournament_q_params: TournamentQuery = Depends(),
                          db=Depends(get_db),
                          tournament_q_model: TournamentQModel = Depends(verify_session_cookie),
                          settings: config.Settings = Depends(get_settings),
                          q: Queue = Depends(get_q)):
    if tournament_q_model["status"] == QueryStatus.fetching:
        return tournament_q_model

    tournament_q_model["status"] = QueryStatus.fetching

    update_res = \
        await db["tournaments"].update_one({"_id": tournament_q_model["_id"]}, {"$set": tournament_q_model})

    if update_res.modified_count == 1:
        q.enqueue(scrape_cmg, tournament_q_model["session_id"])

        return tournament_q_model

    raise HTTPException(status_code=500, detail="Server error - something went wrong processing the query")


@router.post("/tournaments", response_model=TournamentQModel)
async def create_query_session(db=Depends(get_db)):
    new_query = TournamentQModel(session_id=token_urlsafe(16), status=QueryStatus.ready, tournaments=[])
    new_query = jsonable_encoder(new_query)

    inserted = await db["tournaments"].insert_one(new_query)
    created_query = await db["tournaments"].find_one({"_id": inserted.inserted_id})

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_query)
