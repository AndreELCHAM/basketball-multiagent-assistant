import httpx
import json
import os
import sys

def print_section(title):
    print("\n" + "=" * 60)
    print(f"> {title}")
    print("=" * 60)

def test_system_b():
    print_section("Testing System B (Live Web Search)")
    try:
        # Test basic search
        print("\n1. Testing /search (Live News):")
        resp = httpx.post("http://localhost:8001/search", json={
            "query": "Who is currently leading the NBA in scoring for the 2025-26 season?"
        }, timeout=120.0)
        data = resp.json()
        print(f"Status: {data.get('status')}")
        print(f"League detected: {data.get('league')}")
        print(f"Answer snippet: {data.get('answer', '')[:150]}...")
        print(f"Sources: {len(data.get('results', []))}")

        # Test player stats extraction
        print("\n2. Testing /player-stats (Structured Extraction):")
        resp = httpx.post("http://localhost:8001/player-stats", json={
            "player": "Luka Doncic",
            "league": "NBA",
            "stat_type": "season"
        }, timeout=120.0)
        data = resp.json()
        print(f"Status: {data.get('status')}")
        print("Extracted Stats:")
        print(json.dumps(data.get('player_stats', {}), indent=2))
    except Exception as e:
        print(f"[ERROR] Failed to reach System B: {e}\n(Is 'docker-compose up' running?)")

def test_mcp_suspension():
    print_section("Testing MCP Suspension Calculator")
    try:
        # Draymond Green simulation (15 techs in 50 games)
        resp = httpx.post("http://localhost:5002/calculate-suspension", json={
            "fouls_committed": 15,
            "games_played": 50,
            "league": "NBA"
        })
        data = resp.json()
        print(f"Risk Level: {data.get('risk_level')}")
        print(f"Suspension Probability: {data.get('suspension_probability') * 100:.1f}%")
        print(f"Explanation: {data.get('explanation')}")
    except Exception as e:
        print(f"[ERROR] Failed to reach MCP Suspension Calculator: {e}")

def test_mcp_performance():
    print_section("Testing MCP Performance Calculator")
    try:
        # Nikola Jokic simulation (28 pts, 14 reb, 11 ast, 2 stl, 0 blk, 3 tov)
        resp = httpx.post("http://localhost:5003/calculate-performance", json={
            "points": 28,
            "rebounds": 14,
            "assists": 11,
            "steals": 2,
            "blocks": 0,
            "turnovers": 3,
            "fg_made": 11,
            "fg_attempted": 17,
            "ft_made": 5,
            "ft_attempted": 6,
            "minutes": 35.5
        })
        data = resp.json()
        print(f"Grade: {data.get('grade')} ({data.get('grade_description')})")
        print(f"Game Score: {data.get('game_score')}")
        print(f"True Shooting: {data.get('true_shooting_pct')}%")
        print(f"Analysis: {data.get('analysis')}")
    except Exception as e:
        print(f"[ERROR] Failed to reach MCP Performance Calculator: {e}")

if __name__ == "__main__":
    print("Testing microservices (Ensure docker-compose is running!)...")
    test_system_b()
    test_mcp_suspension()
    test_mcp_performance()
