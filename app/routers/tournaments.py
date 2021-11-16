from urllib.parse import urlparse, urlencode

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import conset
from rq import Queue, Retry
from secrets import token_urlsafe

from app.depenencies import get_settings, verify_session_cookie, get_db, get_q
from app import config
from app.jobs import scrape_cmg, scrape_umg
from app.models.tournament_models import TournamentSite, Region, TeamSize, TournamentQModel, QueryStatus

router = APIRouter()


class TournamentQuery:
    def __init__(
            self,
            regions: conset(Region, min_items=1, max_items=3) = Query(...),
            team_sizes: conset(TeamSize, min_items=1, max_items=4, ) = Query(...)
    ):
        self.regions = regions
        self.team_sizes = team_sizes


async def general_team_size(team_sizes):
    t_s = []

    for size in team_sizes:
        if t_s == 1:
            t_s.append("1v1")
        elif t_s == 2:
            t_s.append("2v2")
        elif t_s == 3:
            t_s.append("3v3")
        elif t_s == 4:
            t_s.append("4v4")

    return t_s


async def cmg_team_size(team_sizes):
    if team_sizes == ["1", "2", "3", "4"]:
        return dict(team="all")

    t_s = []
    for s in team_sizes:
        if s == "1":
            t_s.append("solo")
        elif s == "2":
            t_s.append("duo")
        elif (s == "3" or s == "4") and "squad" not in t_s:
            t_s.append("squad")

    t_s = ",".join(t_s)

    return dict(team=t_s)


async def cmg_region(regions):
    new_regions = []

    for region in regions:
        if region == Region.usa:
            new_regions.append("na")
        elif region == Region.europe:
            new_regions.append("eu")
        else:
            new_regions.append("na_eu")

    new_regions = ",".join(new_regions)

    return dict(region=new_regions)


async def build_cmg_url(settings, team_size, regions):
    url_query_build = urlparse(settings.base_cmg_url + settings.cmg_game_path)
    queries = urlencode({**team_size, **regions})
    return url_query_build._replace(query=queries).geturl()


async def enqueue_cmg_job(q, tournament_q_model, settings, tournament_q_params,
                          new_status=QueryStatus.fetching, dependant_job=None):
    cmg_team_sizes = await cmg_team_size(tournament_q_params.team_sizes)
    cmg_regions = await cmg_region(tournament_q_params.regions)
    cmg_url = await build_cmg_url(settings, cmg_team_sizes, cmg_regions)

    job = None

    if dependant_job:
        job = \
            q.enqueue(scrape_cmg, tournament_q_model["session_id"], new_status, cmg_url,
                      retry=Retry(max=3), depends_on=dependant_job)
    else:
        job = q.enqueue(scrape_cmg, tournament_q_model["session_id"], QueryStatus.fetched, cmg_url, retry=Retry(max=3))

    return job


async def enqueue_umg_job(q, tournament_q_model, settings, tournament_q_params,
                          new_status=QueryStatus.fetching, dependant_job=None):
    umg_team_sizes = await general_team_size(tournament_q_params.team_sizes)

    job = None

    if dependant_job:
        job = \
            q.enqueue(scrape_umg, tournament_q_model["session_id"], new_status, umg_team_sizes,
                      tournament_q_params.regions,
                      retry=Retry(max=3), depends_on=dependant_job)
    else:
        job = q.enqueue(scrape_umg, tournament_q_model["session_id"], new_status, umg_team_sizes,
                        tournament_q_params.regions, retry=Retry(max=3))

    return job


@router.get("/tournaments", response_model=TournamentQModel)
async def get_tournaments(tournament_q_params: TournamentQuery = Depends(),
                          db=Depends(get_db),
                          tournament_q_model: TournamentQModel = Depends(verify_session_cookie),
                          settings: config.Settings = Depends(get_settings),
                          q: Queue = Depends(get_q)):
    if tournament_q_model["status"] == QueryStatus.fetching:
        return tournament_q_model

    if tournament_q_model["status"] == QueryStatus.fetched:
        tournament_q_model["status"] = QueryStatus.ready
        new_t_query = tournament_q_model.copy()
        new_t_query["tournaments"] = []

        update_res = \
            await db["tournaments"].update_one({"_id": tournament_q_model["_id"]}, {"$set": new_t_query})

        if update_res.modified_count == 1:
            tournament_q_model["tournaments"].sort(key=lambda t: t["start_time"])
            return tournament_q_model

        raise HTTPException(status_code=500, detail="Server error - something went wrong processing the query")

    tournament_q_model["status"] = QueryStatus.fetching

    update_res = \
        await db["tournaments"].update_one({"_id": tournament_q_model["_id"]}, {"$set": tournament_q_model})

    if update_res.modified_count == 1:
        cmg_job = await enqueue_cmg_job(q, tournament_q_model, settings, tournament_q_params)
        # umg_job = await enqueue_umg_job(q, tournament_q_model, settings, tournament_q_params,
        #                                 dependant_job=cmg_job, new_status=QueryStatus.fetched)

        return tournament_q_model

    raise HTTPException(status_code=500, detail="Server error - something went wrong processing the query")


@router.post("/tournaments", response_model=TournamentQModel)
async def create_query_session(db=Depends(get_db)):
    new_query = TournamentQModel(session_id=token_urlsafe(16), status=QueryStatus.ready, tournaments=[])
    new_query = jsonable_encoder(new_query)

    inserted = await db["tournaments"].insert_one(new_query)
    created_query = await db["tournaments"].find_one({"_id": inserted.inserted_id})

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_query)
