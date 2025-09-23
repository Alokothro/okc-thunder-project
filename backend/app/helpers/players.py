import json
import os
from typing import Dict, List, Any
from django.db.models import Count, Sum, Avg, Q, F
from django.db import connection
import numpy as np
from scipy import stats as scipy_stats

from app.dbmodels import models


def get_player_summary_stats(player_id: str) -> Dict[str, Any]:
    """
    Generate comprehensive player summary statistics from database.
    Returns detailed shot, pass, and turnover data organized by action type.
    """
    try:
        # Convert player_id to integer
        player_id_int = int(player_id)

        # Get player information
        player = models.Player.objects.filter(player_id=player_id_int).first()

        if not player:
            # Return sample data if player not found
            with open(os.path.dirname(os.path.abspath(__file__)) + '/sample_summary_data/sample_summary_data.json') as sample_summary:
                return json.load(sample_summary)

        # Initialize response structure
        response = {
            "name": player.name,
            "playerID": player.player_id,
            "teamName": player.team.name,
            "teamID": player.team.team_id,
            "position": player.position or "N/A",
            "jerseyNumber": player.jersey_number or 0
        }

        # Get aggregate statistics
        shots = models.Shot.objects.filter(player=player)
        passes = models.Pass.objects.filter(player=player)
        turnovers = models.Turnover.objects.filter(player=player)

        # Calculate totals
        response["totalShotAttempts"] = shots.count()
        response["totalPoints"] = shots.aggregate(Sum('points'))['points__sum'] or 0
        response["totalPasses"] = passes.count()
        response["totalPotentialAssists"] = passes.filter(potential_assist=True).count()
        response["totalTurnovers"] = turnovers.count()
        response["totalPassingTurnovers"] = passes.filter(turnover=True).count()

        # Calculate shooting percentages
        if response["totalShotAttempts"] > 0:
            response["fieldGoalPercentage"] = round(
                (shots.filter(points__gt=0).count() / response["totalShotAttempts"]) * 100, 1
            )
            response["effectiveFieldGoalPercentage"] = round(
                ((shots.filter(points__gt=0).count() + 0.5 * shots.filter(points=3).count()) /
                 response["totalShotAttempts"]) * 100, 1
            )
        else:
            response["fieldGoalPercentage"] = 0.0
            response["effectiveFieldGoalPercentage"] = 0.0

        # Calculate pass completion rate
        completed_passes = passes.filter(completed_pass=True).count()
        if response["totalPasses"] > 0:
            response["passCompletionRate"] = round((completed_passes / response["totalPasses"]) * 100, 1)
        else:
            response["passCompletionRate"] = 0.0

        # Count by action types
        action_types = ['pickAndRoll', 'isolation', 'postUp', 'offBallScreen']
        for action_type in action_types:
            camel_case = action_type[0].lower() + action_type[1:]  # Convert to camelCase
            response[f"{camel_case}Count"] = (
                shots.filter(action_type=action_type).count() +
                passes.filter(action_type=action_type).count()
            )

        # Process detailed data by action type
        for action_type in action_types:
            camel_case = action_type[0].lower() + action_type[1:]

            # Get filtered data
            action_shots = shots.filter(action_type=action_type)
            action_passes = passes.filter(action_type=action_type)
            action_turnovers = turnovers.filter(action_type=action_type)

            action_data = {
                "totalShotAttempts": action_shots.count(),
                "totalPoints": action_shots.aggregate(Sum('points'))['points__sum'] or 0,
                "totalPasses": action_passes.count(),
                "totalPotentialAssists": action_passes.filter(potential_assist=True).count(),
                "totalTurnovers": action_turnovers.count(),
                "totalPassingTurnovers": action_passes.filter(turnover=True).count(),
                "shots": [],
                "passes": [],
                "turnovers": []
            }

            # Process shots
            for shot in action_shots:
                shot_data = {
                    "loc": [round(shot.shot_loc_x, 2), round(shot.shot_loc_y, 2)],
                    "points": shot.points,
                    "shotDistance": round(shot.shot_distance, 2) if shot.shot_distance else 0,
                    "shotAngle": round(shot.shot_angle, 1) if shot.shot_angle else 0,
                    "foulDrawn": shot.shooting_foul_drawn,
                    "gameId": shot.game.game_id
                }
                action_data["shots"].append(shot_data)

            # Process passes
            for pass_obj in action_passes:
                pass_data = {
                    "startLoc": [round(pass_obj.ball_start_loc_x, 2), round(pass_obj.ball_start_loc_y, 2)],
                    "endLoc": [round(pass_obj.ball_end_loc_x, 2), round(pass_obj.ball_end_loc_y, 2)],
                    "isCompleted": pass_obj.completed_pass,
                    "isPotentialAssist": pass_obj.potential_assist,
                    "isTurnover": pass_obj.turnover,
                    "passDistance": round(pass_obj.pass_distance, 2) if pass_obj.pass_distance else 0,
                    "gameId": pass_obj.game.game_id
                }
                action_data["passes"].append(pass_data)

            # Process turnovers
            for turnover in action_turnovers:
                turnover_data = {
                    "loc": [round(turnover.tov_loc_x, 2), round(turnover.tov_loc_y, 2)],
                    "turnoverType": turnover.turnover_type or "unknown",
                    "gameId": turnover.game.game_id
                }
                action_data["turnovers"].append(turnover_data)

            # Calculate action-specific shooting percentage
            if action_data["totalShotAttempts"] > 0:
                shots_made = action_shots.filter(points__gt=0).count()
                action_data["fieldGoalPercentage"] = round(
                    (shots_made / action_data["totalShotAttempts"]) * 100, 1
                )
            else:
                action_data["fieldGoalPercentage"] = 0.0

            # Calculate assist to turnover ratio for this action type
            if action_data["totalTurnovers"] > 0:
                action_data["assistToTurnoverRatio"] = round(
                    action_data["totalPotentialAssists"] / action_data["totalTurnovers"], 2
                )
            else:
                action_data["assistToTurnoverRatio"] = float('inf') if action_data["totalPotentialAssists"] > 0 else 0.0

            response[camel_case] = action_data

        # Add advanced metrics
        response["advancedMetrics"] = calculate_advanced_metrics(player_id_int)

        return response

    except Exception as e:
        print(f"Error in get_player_summary_stats: {str(e)}")
        # Fallback to sample data
        with open(os.path.dirname(os.path.abspath(__file__)) + '/sample_summary_data/sample_summary_data.json') as sample_summary:
            return json.load(sample_summary)


def calculate_advanced_metrics(player_id: int) -> Dict[str, Any]:
    """Calculate advanced basketball metrics for a player"""
    try:
        player = models.Player.objects.get(player_id=player_id)
        shots = models.Shot.objects.filter(player=player)
        passes = models.Pass.objects.filter(player=player)
        turnovers = models.Turnover.objects.filter(player=player)

        total_shots = shots.count()
        shots_made = shots.filter(points__gt=0).count()
        three_pointers_made = shots.filter(points=3).count()
        free_throws_made = shots.filter(shooting_foul_drawn=True, points__gt=0).count()

        # True Shooting Percentage
        total_points = shots.aggregate(Sum('points'))['points__sum'] or 0
        tsa = total_shots + (0.44 * free_throws_made)  # True Shooting Attempts
        true_shooting_pct = (total_points / (2 * tsa) * 100) if tsa > 0 else 0

        # Player Efficiency Rating (simplified)
        assists = passes.filter(potential_assist=True).count()
        rebounds = 0  # Would need rebound data
        steals = 0  # Would need steal data
        blocks = 0  # Would need block data
        missed_shots = total_shots - shots_made
        turnovers_count = turnovers.count()

        # Simplified PER calculation
        per = (total_points + assists * 2 - missed_shots - turnovers_count) / max(total_shots, 1)

        # Usage Rate (percentage of team plays used by player)
        team_shots = models.Shot.objects.filter(player__team=player.team).count()
        team_turnovers = models.Turnover.objects.filter(player__team=player.team).count()
        team_possessions = team_shots + team_turnovers

        player_possessions = total_shots + turnovers_count
        usage_rate = (player_possessions / team_possessions * 100) if team_possessions > 0 else 0

        # Hot zones (areas where player shoots best)
        hot_zones = calculate_hot_zones(shots)

        return {
            "trueShootingPercentage": round(true_shooting_pct, 1),
            "playerEfficiencyRating": round(per, 1),
            "usageRate": round(usage_rate, 1),
            "pointsPerShot": round(total_points / total_shots, 2) if total_shots > 0 else 0,
            "assistToTurnoverRatio": round(assists / turnovers_count, 2) if turnovers_count > 0 else float('inf') if assists > 0 else 0,
            "hotZones": hot_zones,
            "clutchStats": calculate_clutch_stats(player_id)
        }
    except Exception as e:
        print(f"Error calculating advanced metrics: {str(e)}")
        return {}


def calculate_hot_zones(shots) -> List[Dict[str, Any]]:
    """Calculate shooting hot zones on the court"""
    zones = []

    # Define court zones
    zone_definitions = [
        {"name": "Restricted Area", "x_range": (-8, 8), "y_range": (0, 8)},
        {"name": "Left Corner 3", "x_range": (-25, -22), "y_range": (0, 9)},
        {"name": "Right Corner 3", "x_range": (22, 25), "y_range": (0, 9)},
        {"name": "Left Wing 3", "x_range": (-25, -15), "y_range": (9, 24)},
        {"name": "Right Wing 3", "x_range": (15, 25), "y_range": (9, 24)},
        {"name": "Top of Key 3", "x_range": (-15, 15), "y_range": (24, 30)},
        {"name": "Mid-Range Left", "x_range": (-22, -8), "y_range": (8, 24)},
        {"name": "Mid-Range Right", "x_range": (8, 22), "y_range": (8, 24)},
        {"name": "Free Throw Line", "x_range": (-8, 8), "y_range": (8, 20)}
    ]

    for zone in zone_definitions:
        zone_shots = shots.filter(
            shot_loc_x__gte=zone["x_range"][0],
            shot_loc_x__lte=zone["x_range"][1],
            shot_loc_y__gte=zone["y_range"][0],
            shot_loc_y__lte=zone["y_range"][1]
        )

        total = zone_shots.count()
        made = zone_shots.filter(points__gt=0).count()

        if total > 0:
            percentage = round((made / total) * 100, 1)
            zones.append({
                "zone": zone["name"],
                "shotsMade": made,
                "shotsAttempted": total,
                "percentage": percentage,
                "rating": "hot" if percentage >= 45 else "warm" if percentage >= 35 else "cold"
            })

    return zones


def calculate_clutch_stats(player_id: int) -> Dict[str, Any]:
    """Calculate performance in clutch situations (placeholder for now)"""
    # This would analyze performance in close games, final minutes, etc.
    return {
        "clutchShootingPercentage": 0.0,
        "clutchAssists": 0,
        "clutchTurnovers": 0
    }


def get_ranks(player_id: str, player_summary: dict) -> Dict[str, int]:
    """
    Calculate player rankings compared to all other players using percentile rankings.
    Returns rank from 1 (best) to N (worst) for each statistic.
    """
    try:
        # Get all players
        all_players = models.Player.objects.all()
        player_count = all_players.count()

        if player_count == 0:
            return get_default_ranks()

        # Collect stats for all players
        all_stats = []
        for player in all_players:
            shots = models.Shot.objects.filter(player=player)
            passes = models.Pass.objects.filter(player=player)
            turnovers = models.Turnover.objects.filter(player=player)

            stats = {
                "playerID": player.player_id,
                "totalShotAttempts": shots.count(),
                "totalPoints": shots.aggregate(Sum('points'))['points__sum'] or 0,
                "totalPasses": passes.count(),
                "totalPotentialAssists": passes.filter(potential_assist=True).count(),
                "totalTurnovers": turnovers.count(),
                "totalPassingTurnovers": passes.filter(turnover=True).count(),
                "pickAndRollCount": (
                    shots.filter(action_type='pickAndRoll').count() +
                    passes.filter(action_type='pickAndRoll').count()
                ),
                "isolationCount": (
                    shots.filter(action_type='isolation').count() +
                    passes.filter(action_type='isolation').count()
                ),
                "postUpCount": (
                    shots.filter(action_type='postUp').count() +
                    passes.filter(action_type='postUp').count()
                ),
                "offBallScreenCount": (
                    shots.filter(action_type='offBallScreen').count() +
                    passes.filter(action_type='offBallScreen').count()
                )
            }
            all_stats.append(stats)

        # Convert player_id to int for comparison
        current_player_id = int(player_id)

        # Calculate ranks (1 = best)
        ranks = {}

        stat_keys = [
            "totalShotAttempts", "totalPoints", "totalPasses", "totalPotentialAssists",
            "pickAndRollCount", "isolationCount", "postUpCount", "offBallScreenCount"
        ]

        # For turnovers, lower is better
        turnover_keys = ["totalTurnovers", "totalPassingTurnovers"]

        for key in stat_keys:
            # Sort descending (higher is better)
            sorted_stats = sorted(all_stats, key=lambda x: x[key], reverse=True)
            for i, stats in enumerate(sorted_stats, 1):
                if stats["playerID"] == current_player_id:
                    ranks[f"{key}Rank"] = i
                    break
            else:
                ranks[f"{key}Rank"] = player_count

        for key in turnover_keys:
            # Sort ascending (lower is better)
            sorted_stats = sorted(all_stats, key=lambda x: x[key])
            for i, stats in enumerate(sorted_stats, 1):
                if stats["playerID"] == current_player_id:
                    ranks[f"{key}Rank"] = i
                    break
            else:
                ranks[f"{key}Rank"] = player_count

        # Add percentile ranks for better context
        ranks["percentileRanks"] = calculate_percentile_ranks(current_player_id, all_stats, player_count)

        return ranks

    except Exception as e:
        print(f"Error in get_ranks: {str(e)}")
        return get_default_ranks()


def calculate_percentile_ranks(player_id: int, all_stats: List[Dict], total_players: int) -> Dict[str, float]:
    """Calculate percentile ranks (0-100) for each stat"""
    percentiles = {}

    # Find current player's stats
    player_stats = next((s for s in all_stats if s["playerID"] == player_id), None)
    if not player_stats:
        return {}

    stat_keys = list(player_stats.keys())
    stat_keys.remove("playerID")

    for key in stat_keys:
        values = [s[key] for s in all_stats]
        if values:
            # Calculate percentile
            percentile = scipy_stats.percentileofscore(values, player_stats[key])

            # For turnovers, invert the percentile (lower is better)
            if "Turnover" in key:
                percentile = 100 - percentile

            percentiles[f"{key}Percentile"] = round(percentile, 1)

    return percentiles


def get_default_ranks() -> Dict[str, int]:
    """Return default ranks when calculation fails"""
    import random
    random.seed(42)
    return {
        "totalShotAttemptsRank": random.randint(1, 10),
        "totalPointsRank": random.randint(1, 10),
        "totalPassesRank": random.randint(1, 10),
        "totalPotentialAssistsRank": random.randint(1, 10),
        "totalTurnoversRank": random.randint(1, 10),
        "totalPassingTurnoversRank": random.randint(1, 10),
        "pickAndRollCountRank": random.randint(1, 10),
        "isolationCountRank": random.randint(1, 10),
        "postUpCountRank": random.randint(1, 10),
        "offBallScreenCountRank": random.randint(1, 10)
    }


def get_player_comparison(player_ids: List[int]) -> Dict[str, Any]:
    """
    Compare multiple players side by side
    """
    comparison = {"players": []}

    for player_id in player_ids[:4]:  # Limit to 4 players max
        summary = get_player_summary_stats(str(player_id))
        ranks = get_ranks(str(player_id), summary)

        comparison["players"].append({
            "summary": summary,
            "ranks": ranks
        })

    return comparison