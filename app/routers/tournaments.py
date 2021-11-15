from bson import ObjectId
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, HttpUrl, Field, conset
from typing import List
from enum import Enum, IntEnum
from rq import Queue
from secrets import token_urlsafe

from app.depenencies import get_settings, verify_session_cookie, get_db, get_q
from app import config
from app.jobs import scrape_cmg

router = APIRouter()


class TournamentSite(str, Enum):
    cmg = "CMG"
    gb = "GB"
    umg = "UMG"

    class Config:
        use_enum_values = True


class Region(str, Enum):
    europe = "EU"
    usa = "NA"
    usa_europe = "NA+EU"

    class Config:
        use_enum_values = True


class TeamSize(IntEnum):
    singles = 1
    doubles = 2
    threes = 3
    fours = 4


class QueryStatus(str, Enum):
    fetching = "fetching"
    failed = "failed"
    ready = "ready"

    class Config:
        use_enum_values = True


class Tournament(BaseModel):
    site: TournamentSite
    name: str
    url: HttpUrl
    region: Region
    prize: str
    start_time: float

    def __str__(self) -> str:
        return f'name={self.name},url={self.url},region={self.region},prize={self.prize},start_time={self.start_time}'


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


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class TournamentQModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    session_id: str = Field(...)
    status: QueryStatus = Field(...)
    tournaments: List[Tournament] = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BlankTournamentQModel(BaseModel):
    session_id: str = ""
    status: QueryStatus = QueryStatus.fetching
    tournaments: List[Tournament] = []

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


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
        q.enqueue(scrape_cmg, tournament_q_model["session_id"], db)

        return tournament_q_model

    raise HTTPException(status_code=500, detail="Server error - something went wrong processing the query")


@router.post("/tournaments", response_model=TournamentQModel)
async def create_query_session(db=Depends(get_db)):
    new_query = TournamentQModel(session_id=token_urlsafe(16), status=QueryStatus.ready, tournaments=[])
    new_query = jsonable_encoder(new_query)

    inserted = await db["tournaments"].insert_one(new_query)
    created_query = await db["tournaments"].find_one({"_id": inserted.inserted_id})

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_query)
