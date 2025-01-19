from typing import List, Dict, Any, Optional, TypedDict
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class Match(BaseModel):
    id: str = Field(description="Unique identifier for the match")
    sport_key: str = Field(description="Key representing the sport or tournament")
    matchId: str = Field(description="A unique identifier for the match, including teams and date")
    teams: List[str] = Field(description="List of teams participating in the match")
    start: str = Field(description="Match start time in ISO 8601 format")
    odd: float = Field(description="The odd value")
    sign: str = Field(description="The odd sign")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sport_key": self.sport_key,
            "matchId": self.matchId,
            "teams": self.teams,
            "start": self.start,
            "odd": self.odd,
            "sign": self.sign,
        }
    
class ProcessActionResult(TypedDict):
    payslip: List[Match]
    message: str
    
class Response(BaseModel):
    status: str = Field(description="The status of the response, can be either 'Ok', 'match-not-found', 'api-error', 'bet-amount-not-found', 'bet-placed'")
    message: str = Field(description="A message to give a human response to the user")
    sign: Optional[str] = Field(None, description="The sign of the match, can be either 'home', 'away', 'draw', 'over', 'under'")
    match_id: Optional[str] = Field(None, description="The id of the match to be added or removed")
    amount:  Optional[float] = Field(None,description="The total amount of the payslip")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "sign": self.sign,
            "match_id": self.match_id,
            "amount": self.amount,
        }
    

class TeamNames(BaseModel):
    team_names: List[str] = Field(description="List of team names")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_names": self.team_names,
        }

class Sign(BaseModel):
    sign: str = Field(description="The sign of the match")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign": self.sign,
        }
# Create a PydanticOutputParser for the Response model

response_parser = PydanticOutputParser(pydantic_object=Response)
tea_names_parser = PydanticOutputParser(pydantic_object=TeamNames)
sign_parser = PydanticOutputParser(pydantic_object=Sign)
