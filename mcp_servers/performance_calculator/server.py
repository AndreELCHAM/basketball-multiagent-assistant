

import logging
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Tool: Player Performance Calculator",
    description="Deterministic player performance scorer using Game Score and efficiency metrics",
    version="1.0.0",
)



class PerformanceRequest(BaseModel):
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    steals: int = 0
    blocks: int = 0
    turnovers: int = 0
    fg_made: int = 0
    fg_attempted: int = 0
    ft_made: int = 0
    ft_attempted: int = 0
    minutes: float = 0
    personal_fouls: int = 0
    offensive_rebounds: Optional[int] = None
    defensive_rebounds: Optional[int] = None


class PerformanceResponse(BaseModel):

    player_stats: dict

    
    game_score: float
    efficiency_rating: float
    true_shooting_pct: Optional[float]
    effective_fg_pct: Optional[float]

    per_36_stats: dict

    
    grade: str
    grade_description: str
    analysis: str
    benchmarks: dict

    source: str = "mcp-performance-calculator"




GRADE_THRESHOLDS = [
    (40.0, "A+", "Legendary performance — all-time level game"),
    (30.0, "A",  "Elite performance — MVP caliber"),
    (25.0, "A-", "Outstanding performance — All-Star level"),
    (20.0, "B+", "Very strong performance — starter quality"),
    (15.0, "B",  "Solid above-average performance"),
    (10.0, "B-", "Good, dependable performance"),
    (7.0,  "C+", "Average performance"),
    (4.0,  "C",  "Below-average performance"),
    (1.0,  "C-", "Poor performance"),
    (0.0,  "D",  "Minimal positive contribution"),
    (-999, "F",  "Negative contribution to the team"),
]

BENCHMARKS = {
    "legendary": 45.0,
    "elite_mvp": 30.0,
    "all_star": 20.0,
    "solid_starter": 12.0,
    "rotation_player": 7.0,
    "average_nba": 10.0,
}




@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mcp-performance-calculator"}


@app.post("/calculate-performance", response_model=PerformanceResponse)
def calculate_performance(request: PerformanceRequest):


    orb = request.offensive_rebounds if request.offensive_rebounds is not None else 0
    drb = request.defensive_rebounds if request.defensive_rebounds is not None else 0


    if orb == 0 and drb == 0 and request.rebounds > 0:
        orb = round(request.rebounds * 0.3)
        drb = request.rebounds - orb
    game_score = (
        request.points
        + 0.4 * request.fg_made
        - 0.7 * request.fg_attempted
        - 0.4 * (request.ft_attempted - request.ft_made)
        + 0.7 * orb
        + 0.3 * drb
        + request.steals
        + 0.7 * request.assists
        + 0.7 * request.blocks
        - 0.4 * request.personal_fouls
        - request.turnovers
    )
    game_score = round(game_score, 1)


    missed_fg = request.fg_attempted - request.fg_made
    missed_ft = request.ft_attempted - request.ft_made
    efficiency = (
        request.points + request.rebounds + request.assists
        + request.steals + request.blocks
        - request.turnovers - missed_fg - missed_ft
    )

    true_shooting = None
    effective_fg = None

    if request.fg_attempted > 0:
        effective_fg = round(
            (request.fg_made + 0.5 * max(0, request.points - 2 * request.fg_made - request.ft_made))
            / request.fg_attempted * 100, 1
        )

        effective_fg = round(request.fg_made / request.fg_attempted * 100, 1)

    tsa = request.fg_attempted + 0.44 * request.ft_attempted
    if tsa > 0:
        true_shooting = round(request.points / (2 * tsa) * 100, 1)

    per_36 = {}
    if request.minutes > 0:
        scale = 36.0 / request.minutes
        per_36 = {
            "points": round(request.points * scale, 1),
            "rebounds": round(request.rebounds * scale, 1),
            "assists": round(request.assists * scale, 1),
            "steals": round(request.steals * scale, 1),
            "blocks": round(request.blocks * scale, 1),
            "turnovers": round(request.turnovers * scale, 1),
        }

    grade = "F"
    grade_desc = "Negative contribution"
    for threshold, g, desc in GRADE_THRESHOLDS:
        if game_score >= threshold:
            grade = g
            grade_desc = desc
            break


    analysis_parts = []

    analysis_parts.append(
        f"Game Score of {game_score} — {grade_desc.lower()}."
    )

    if request.points >= 25:
        analysis_parts.append(f"Elite scoring output with {request.points} points.")
    elif request.points >= 15:
        analysis_parts.append(f"Solid scoring with {request.points} points.")

    if request.assists >= 8:
        analysis_parts.append(f"Exceptional playmaking with {request.assists} assists.")
    elif request.assists >= 5:
        analysis_parts.append(f"Good court vision with {request.assists} assists.")

    if request.rebounds >= 10:
        analysis_parts.append(f"Dominant on the boards with {request.rebounds} rebounds.")

    if request.steals + request.blocks >= 4:
        analysis_parts.append(
            f"Strong defensive impact with {request.steals} steals and {request.blocks} blocks."
        )

    if request.turnovers >= 5:
        analysis_parts.append(f"Ball security concern with {request.turnovers} turnovers.")

    if true_shooting and true_shooting >= 60:
        analysis_parts.append(f"Excellent shooting efficiency ({true_shooting}% TS).")
    elif true_shooting and true_shooting < 45:
        analysis_parts.append(f"Poor shooting efficiency ({true_shooting}% TS).")

    analysis = " ".join(analysis_parts)

    player_stats = {
        "points": request.points,
        "rebounds": request.rebounds,
        "assists": request.assists,
        "steals": request.steals,
        "blocks": request.blocks,
        "turnovers": request.turnovers,
        "fg": f"{request.fg_made}/{request.fg_attempted}",
        "ft": f"{request.ft_made}/{request.ft_attempted}",
        "minutes": request.minutes,
        "personal_fouls": request.personal_fouls,
    }

    logger.info(
        f"Performance calc: GmSc={game_score}, Eff={efficiency}, "
        f"Grade={grade}, TS%={true_shooting}"
    )

    return PerformanceResponse(
        player_stats=player_stats,
        game_score=game_score,
        efficiency_rating=float(efficiency),
        true_shooting_pct=true_shooting,
        effective_fg_pct=effective_fg,
        per_36_stats=per_36,
        grade=grade,
        grade_description=grade_desc,
        analysis=analysis,
        benchmarks=BENCHMARKS,
    )
