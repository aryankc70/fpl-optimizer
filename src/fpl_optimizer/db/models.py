from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from fpl_optimizer.db.session import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)  # FPL's own team id
    name: Mapped[str] = mapped_column(String(50))
    short_name: Mapped[str] = mapped_column(String(5))
    strength: Mapped[int] = mapped_column(Integer, default=0)

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

    __table_args__ = (
        UniqueConstraint("player_id", "season", "gameweek_id", name="uq_player_season_gw"),
    )

    player: Mapped["Player"] = relationship(back_populates="gameweek_stats")