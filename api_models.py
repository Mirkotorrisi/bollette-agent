from typing import List, Optional

from pydantic import BaseModel, Field


class ProcessInput(BaseModel):
    input: str = Field(..., min_length=1, description="Natural language action from the user")
    session: Optional[str] = Field(default=None, description="Session id returned by the first call")


class MatchOut(BaseModel):
    id: Optional[str] = None
    sport_key: Optional[str] = None
    matchId: Optional[str] = None
    teams: Optional[List[str]] = None
    start: Optional[str] = None
    odd: Optional[float] = None
    sign: Optional[str] = None


class ProcessResponse(BaseModel):
    id: Optional[str] = None
    message: str
    payslip: Optional[List[MatchOut]] = None
    amount: Optional[float] = None
    max_win: Optional[float] = None
    multiplier: Optional[float] = None


class ErrorResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
