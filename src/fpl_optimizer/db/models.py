from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fpl_optimizer.db.session import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    short_name: Mapped[str] = mapped_column(String(5))

    strength_overall_home: Mapped[int] = mapped_column(Integer, default=0)
    strength_overall_away: Mapped[int] = mapped_column(Integer, default=0)
    strength_attack_home: Mapped[int] = mapped_column(Integer, default=0)
    strength_attack_away: Mapped[int] = mapped_column(Integer, default=0)
    strength_defence_home: Mapped[int] = mapped_column(Integer, default=0)
    strength_defence_away: Mapped[int] = mapped_column(Integer, default=0)

    players: Mapped[list["Player"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)  # FPL's own player id
    first_name: Mapped[str] = mapped_column(String(50))
    second_name: Mapped[str] = mapped_column(String(50))
    web_name: Mapped[str] = mapped_column(String(50))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    position: Mapped[str] = mapped_column(String(3))  # GKP, DEF, MID, FWD
    now_cost: Mapped[float] = mapped_column(Float)  # in £m
    

    team: Mapped["Team"] = relationship(back_populates="players")
    gameweek_stats: Mapped[list["PlayerGameweekStat"]] = relationship(back_populates="player")

    status: Mapped[str] = mapped_column(String(1), default="a")  # a=available, d=doubtful, i=injured, s=suspended, u=unavailable
    chance_of_playing_next_round: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100, NULL if fully fit


class Gameweek(Base):
    __tablename__ = "gameweeks"

    id: Mapped[int] = mapped_column(primary_key=True)  # 1 through 38
    name: Mapped[str] = mapped_column(String(20))
    deadline_time: Mapped[datetime] = mapped_column(DateTime)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False)


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(primary_key=True)  # FPL's own fixture id
    gameweek_id: Mapped[int | None] = mapped_column(ForeignKey("gameweeks.id"), nullable=True)
    team_h_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team_h_difficulty: Mapped[int] = mapped_column(Integer, default=0)
    team_a_difficulty: Mapped[int] = mapped_column(Integer, default=0)
    kickoff_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished: Mapped[bool] = mapped_column(Boolean, default=False)
    team_h_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_a_score: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PlayerGameweekStat(Base):
    __tablename__ = "player_gameweek_stats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    gameweek_id: Mapped[int] = mapped_column(Integer)  # gameweek NUMBER (1-38), not a strict FK
    season: Mapped[str] = mapped_column(String(10))  # e.g. "2025-26"

    minutes: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    goals_scored: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    clean_sheets: Mapped[int] = mapped_column(Integer, default=0)
    expected_goals: Mapped[float] = mapped_column(Float, default=0.0)
    expected_assists: Mapped[float] = mapped_column(Float, default=0.0)
    bonus: Mapped[int] = mapped_column(Integer, default=0)
    value: Mapped[float] = mapped_column(Float)
    clearances_blocks_interceptions: Mapped[int] = mapped_column(Integer, default=0)
    tackles: Mapped[int] = mapped_column(Integer, default=0)
    recoveries: Mapped[int] = mapped_column(Integer, default=0)
    defensive_contribution: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("player_id", "season", "gameweek_id", name="uq_player_season_gw"),
    )

    player: Mapped["Player"] = relationship(back_populates="gameweek_stats")

class PlayerPrediction(Base):
    __tablename__ = "player_predictions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    season: Mapped[str] = mapped_column(String(10))       # season being predicted FOR
    gameweek_id: Mapped[int] = mapped_column(Integer)      # gameweek being predicted FOR
    predicted_points: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("player_id", "season", "gameweek_id", name="uq_prediction_player_season_gw"),
    )

class HistoricalFixtureResult(Base):
    __tablename__ = "historical_fixture_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    season: Mapped[str] = mapped_column(String(10))
    gameweek_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    team_h_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team_h_score: Mapped[int] = mapped_column(Integer)
    team_a_score: Mapped[int] = mapped_column(Integer)

class UserSquad(Base):
    __tablename__ = "user_squad"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    player_ids: Mapped[str] = mapped_column(String(500))  # comma-separated player ids
    free_transfers: Mapped[int] = mapped_column(Integer, default=1)
    bank: Mapped[float] = mapped_column(Float, default=0.0)  # leftover budget, in £m
    last_updated_gameweek: Mapped[int] = mapped_column(Integer, default=1)