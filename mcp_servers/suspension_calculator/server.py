

import logging
import math
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Tool: Suspension Probability Calculator",
    description="Deterministic suspension risk calculator for basketball leagues",
    version="1.0.0",
)




LEAGUE_THRESHOLDS = {
    "NBA": {
        "technical_foul_threshold": 16,
        "flagrant_foul_threshold": 5,
        "regular_season_games": 82,
        "description": "NBA: 16th technical foul = 1-game suspension, then every other tech",
    },
    "FIBA": {
        "technical_foul_threshold": 5,
        "flagrant_foul_threshold": 3,
        "regular_season_games": 34,
        "description": "FIBA: 5 technicals in a competition phase = suspension",
    },
    "NCAA": {
        "technical_foul_threshold": 5,
        "flagrant_foul_threshold": 3,
        "regular_season_games": 31,
        "description": "NCAA: 5th technical = ejection, accumulation rules vary by conference",
    },
    "FIBA_3X3": {
        "technical_foul_threshold": 3,
        "flagrant_foul_threshold": 2,
        "regular_season_games": 20,
        "description": "FIBA 3x3: strict technical limit due to shorter game format",
    },
}




class SuspensionRequest(BaseModel):
    fouls_committed: int
    games_played: int
    total_season_games: Optional[int] = None
    foul_threshold: Optional[int] = None
    league: str = "NBA"


class SuspensionResponse(BaseModel):
    fouls_committed: int
    games_played: int
    total_season_games: int
    foul_threshold: int
    league: str
    fouls_per_game: float
    projected_total_fouls: float
    games_until_suspension: Optional[int]
    suspension_probability: float
    risk_level: str
    explanation: str
    league_rule: str
    source: str = "mcp-suspension-calculator"




@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mcp-suspension-calculator"}


@app.post("/calculate-suspension", response_model=SuspensionResponse)
def calculate_suspension(request: SuspensionRequest):

    league = request.league.upper()
    league_config = LEAGUE_THRESHOLDS.get(league, LEAGUE_THRESHOLDS["NBA"])

    total_season_games = request.total_season_games or league_config["regular_season_games"]
    foul_threshold = request.foul_threshold or league_config["technical_foul_threshold"]
    league_rule = league_config["description"]

    fouls = request.fouls_committed
    games = request.games_played

    logger.info(
        f"Calculating suspension: {fouls} fouls in {games} games, "
        f"threshold={foul_threshold}, season={total_season_games} games"
    )

 
    if games <= 0:
        return SuspensionResponse(
            fouls_committed=fouls,
            games_played=games,
            total_season_games=total_season_games,
            foul_threshold=foul_threshold,
            league=league,
            fouls_per_game=0.0,
            projected_total_fouls=float(fouls),
            games_until_suspension=None,
            suspension_probability=0.0,
            risk_level="UNKNOWN",
            explanation="Cannot calculate with 0 games played.",
            league_rule=league_rule,
        )

    if fouls >= foul_threshold:
        return SuspensionResponse(
            fouls_committed=fouls,
            games_played=games,
            total_season_games=total_season_games,
            foul_threshold=foul_threshold,
            league=league,
            fouls_per_game=round(fouls / games, 3),
            projected_total_fouls=float(fouls),
            games_until_suspension=0,
            suspension_probability=1.0,
            risk_level="SUSPENDED",
            explanation=(
                f"Player has already reached the {foul_threshold}-foul threshold "
                f"with {fouls} fouls in {games} games. Suspension is active."
            ),
            league_rule=league_rule,
        )


    fouls_per_game = fouls / games
    remaining_games = total_season_games - games

    if remaining_games <= 0:
        return SuspensionResponse(
            fouls_committed=fouls,
            games_played=games,
            total_season_games=total_season_games,
            foul_threshold=foul_threshold,
            league=league,
            fouls_per_game=round(fouls_per_game, 3),
            projected_total_fouls=float(fouls),
            games_until_suspension=None,
            suspension_probability=0.0,
            risk_level="SAFE",
            explanation=(
                f"Season is over. Player finished with {fouls} fouls, "
                f"below the {foul_threshold}-foul threshold."
            ),
            league_rule=league_rule,
        )

    projected_total = fouls + (fouls_per_game * remaining_games)

    fouls_remaining = foul_threshold - fouls
    if fouls_per_game > 0:
        games_until = math.ceil(fouls_remaining / fouls_per_game)
    else:
        games_until = None


    lambda_remaining = fouls_per_game * remaining_games
    fouls_needed = foul_threshold - fouls
    suspension_prob = _poisson_cdf_complement(lambda_remaining, fouls_needed)

    if suspension_prob >= 0.85:
        risk_level = "CRITICAL"
    elif suspension_prob >= 0.60:
        risk_level = "HIGH"
    elif suspension_prob >= 0.30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"


    explanation = (
        f"The player has accumulated {fouls} fouls in {games} games "
        f"(rate: {fouls_per_game:.2f}/game). "
        f"At this pace, they are projected to reach {projected_total:.1f} fouls "
        f"by season end ({total_season_games} games). "
        f"The {league} suspension threshold is {foul_threshold} fouls. "
    )

    if games_until is not None and games_until <= remaining_games:
        explanation += (
            f"At the current rate, they would hit the threshold in approximately "
            f"{games_until} more games (game {games + games_until} of the season). "
        )
    elif games_until is not None:
        explanation += (
            f"At the current rate, they would need {games_until} more games to reach "
            f"the threshold, which extends beyond the remaining {remaining_games} games. "
        )

    explanation += f"Statistical suspension probability: {suspension_prob:.1%}. Risk: {risk_level}."

    return SuspensionResponse(
        fouls_committed=fouls,
        games_played=games,
        total_season_games=total_season_games,
        foul_threshold=foul_threshold,
        league=league,
        fouls_per_game=round(fouls_per_game, 3),
        projected_total_fouls=round(projected_total, 1),
        games_until_suspension=games_until,
        suspension_probability=round(suspension_prob, 4),
        risk_level=risk_level,
        explanation=explanation,
        league_rule=league_rule,
    )


def _poisson_cdf_complement(lam: float, k: int) -> float:
    if lam <= 0:
        return 0.0
    if k <= 0:
        return 1.0
    cdf = 0.0
    for i in range(k):
        log_pmf = -lam + i * math.log(lam) - math.lgamma(i + 1)
        cdf += math.exp(log_pmf)

    return max(0.0, min(1.0, 1.0 - cdf))
