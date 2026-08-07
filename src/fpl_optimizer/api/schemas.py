from pydantic import BaseModel


class PlayerPredictionOut(BaseModel):
    player_id: int
    web_name: str
    position: str
    team_name: str
    now_cost: float
    predicted_points: float
    status: str
    chance_of_playing: int | None

    class Config:
        from_attributes = True


class SquadPlayerOut(BaseModel):
    player_id: int
    web_name: str
    position: str
    cost: float
    predicted_points: float
    status: str


class SquadOut(BaseModel):
    total_cost: float
    total_predicted_points: float
    players: list[SquadPlayerOut]


class LineupOut(BaseModel):
    formation: str
    starting_xi: list[SquadPlayerOut]
    bench: list[SquadPlayerOut]
    captain: SquadPlayerOut
    vice_captain: SquadPlayerOut
    base_points: float
    points_with_captain: float


class HitEvaluationRequest(BaseModel):
    outgoing_player_id: int
    incoming_player_id: int
    num_hits: int = 1


class HitEvaluationOut(BaseModel):
    outgoing_name: str
    incoming_name: str
    outgoing_3gw_projection: float
    incoming_3gw_projection: float
    net_gain: float
    hit_cost: int
    recommendation: str
    reasoning: str


class ChipGuidanceOut(BaseModel):
    gameweek: int
    windows: list[dict]