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
    teams:  Optional[List[str]] = Field(None,description="The team or teams to be added to the payslip")
    sign: Optional[str] = Field(None, description="The sign of the match")
    removed_match_id: Optional[str] = Field(None, description="The id of the match to be removed")
    amount:  Optional[float] = Field(None,description="The total amount of the payslip")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "teams": self.teams,
            "sign": self.sign,
            "removed_match_id": self.removed_match_id,
            "amount": self.amount,
        }
# Create a PydanticOutputParser for the Response model

response_parser = PydanticOutputParser(pydantic_object=Response)
