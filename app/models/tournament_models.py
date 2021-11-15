from pydantic import BaseModel, HttpUrl, Field, conset
from typing import List
from enum import Enum, IntEnum
from bson import ObjectId


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
    fetched = "fetched"

    class Config:
        use_enum_values = True


class Tournament(BaseModel):
    site: TournamentSite
    name: str
    url: HttpUrl
    region: str
    prize: str
    start_time: float

    def __str__(self) -> str:
        return f'name={self.name},url={self.url},region={self.region},prize={self.prize},start_time={self.start_time}'


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
