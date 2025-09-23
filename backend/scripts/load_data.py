#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Loading Script for NBA Player Statistics
This script loads JSON data into the PostgreSQL database with validation and error handling.
It ensures idempotent operations - can be run multiple times without duplicating data.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.db import transaction, IntegrityError
from django.utils import timezone
from app.dbmodels.models import Team, Player, Game, Shot, Pass, Turnover, PlayerGameStats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NBADataLoader:
    """Main class for loading NBA data into the database"""

    def __init__(self, data_dir='raw_data'):
        self.data_dir = Path(data_dir)
        self.stats = {
            'teams_loaded': 0,
            'players_loaded': 0,
            'games_loaded': 0,
            'shots_loaded': 0,
            'passes_loaded': 0,
            'turnovers_loaded': 0,
            'errors': 0
        }

    def load_all(self):
        """Main method to load all data"""
        logger.info("Starting data loading process...")

        try:
            # Load data in correct order due to foreign key constraints
            self.load_teams()
            self.load_games()
            self.load_players()
            self.calculate_game_stats()

            logger.info("Data loading completed successfully!")
            self.print_summary()

        except Exception as e:
            logger.error(f"Error during data loading: {str(e)}")
            raise

    def load_teams(self):
        """Load team data from JSON file"""
        logger.info("Loading teams...")
        teams_file = self.data_dir / 'teams.json'

        with open(teams_file, 'r') as f:
            teams_data = json.load(f)

        for team_data in teams_data:
            try:
                team, created = Team.objects.update_or_create(
                    team_id=team_data['team_id'],  # Fixed field name
                    defaults={
                        'name': team_data['name'],
                        'abbreviation': team_data.get('abbreviation', ''),
                        'city': team_data.get('city', ''),
                        'conference': team_data.get('conference', ''),
                        'division': team_data.get('division', '')
                    }
                )
                if created:
                    self.stats['teams_loaded'] += 1
                    logger.debug(f"Created team: {team.name}")
                else:
                    logger.debug(f"Updated team: {team.name}")

            except Exception as e:
                logger.error(f"Error loading team {team_data.get('team_id')}: {str(e)}")
                self.stats['errors'] += 1

    def load_games(self):
        """Load game data from JSON file"""
        logger.info("Loading games...")
        games_file = self.data_dir / 'games.json'

        with open(games_file, 'r') as f:
            games_data = json.load(f)

        # Ensure we have at least default teams for games
        default_home_team, _ = Team.objects.get_or_create(
            team_id=1,
            defaults={'name': 'Home Team'}
        )
        default_away_team, _ = Team.objects.get_or_create(
            team_id=2,
            defaults={'name': 'Away Team'}
        )

        for game_data in games_data:
            try:
                # Parse game date
                game_date = timezone.now()  # Default to current time
                if 'date' in game_data:
                    try:
                        game_date = datetime.strptime(game_data['date'], '%Y-%m-%d')
                        game_date = timezone.make_aware(game_date)
                    except:
                        pass

                game, created = Game.objects.update_or_create(
                    game_id=game_data['id'],
                    defaults={
                        'game_date': game_date,
                        'home_team': Team.objects.filter(team_id=game_data.get('home_team_id', 1)).first() or default_home_team,
                        'away_team': Team.objects.filter(team_id=game_data.get('away_team_id', 2)).first() or default_away_team,
                        'season': game_data.get('season', '2023-24'),
                        'game_type': game_data.get('game_type', 'practice')
                    }
                )
                if created:
                    self.stats['games_loaded'] += 1
                    logger.debug(f"Created game: {game.game_id}")

            except Exception as e:
                logger.error(f"Error loading game {game_data.get('id')}: {str(e)}")
                self.stats['errors'] += 1

    def load_players(self):
        """Load player data including shots, passes, and turnovers"""
        logger.info("Loading players and their statistics...")
        players_file = self.data_dir / 'players.json'

        with open(players_file, 'r') as f:
            players_data = json.load(f)

        for player_data in players_data:
            try:
                with transaction.atomic():
                    # Load player
                    player = self.load_player(player_data)

                    # Load shots
                    self.load_player_shots(player, player_data.get('shots', []))

                    # Load passes
                    self.load_player_passes(player, player_data.get('passes', []))

                    # Load turnovers
                    self.load_player_turnovers(player, player_data.get('turnovers', []))

            except Exception as e:
                logger.error(f"Error loading player {player_data.get('name')}: {str(e)}")
                self.stats['errors'] += 1

    def load_player(self, player_data):
        """Load individual player"""
        team = Team.objects.filter(team_id=player_data.get('team_id')).first()
        if not team:
            # Create a unique team for unknown team IDs
            team_id = player_data.get('team_id', 999)
            team, _ = Team.objects.get_or_create(
                team_id=team_id,
                defaults={'name': f'Team {team_id}'}
            )

        player, created = Player.objects.update_or_create(
            player_id=player_data['player_id'],
            defaults={
                'name': player_data['name'],
                'team': team,
                'position': player_data.get('position'),
                'jersey_number': player_data.get('jersey_number'),
                'height': player_data.get('height'),
                'weight': player_data.get('weight'),
                'birth_date': None  # Can be parsed if provided
            }
        )

        if created:
            self.stats['players_loaded'] += 1
            logger.debug(f"Created player: {player.name}")

        return player

    def load_player_shots(self, player, shots_data):
        """Load shot data for a player"""
        for shot_data in shots_data:
            try:
                # Get or create game
                game = Game.objects.filter(game_id=shot_data.get('game_id')).first()
                if not game:
                    game, _ = Game.objects.get_or_create(
                        game_id=shot_data.get('game_id', 0),
                        defaults={
                            'game_date': timezone.now(),
                            'home_team_id': 1,
                            'away_team_id': 2,
                            'season': '2023-24',
                            'game_type': 'practice'
                        }
                    )

                # Check if shot already exists
                shot, created = Shot.objects.get_or_create(
                    shot_id=shot_data.get('id'),
                    defaults={
                        'player': player,
                        'game': game,
                        'action_type': shot_data.get('action_type', 'unknown'),
                        'points': shot_data.get('points', 0),
                        'shot_loc_x': shot_data.get('shot_loc_x', 0),
                        'shot_loc_y': shot_data.get('shot_loc_y', 0),
                        'shooting_foul_drawn': shot_data.get('shooting_foul_drawn', False),
                        'quarter': shot_data.get('quarter'),
                        'time_remaining': shot_data.get('time_remaining'),
                        'shot_clock': shot_data.get('shot_clock')
                    }
                )

                if created:
                    self.stats['shots_loaded'] += 1

            except Exception as e:
                logger.error(f"Error loading shot {shot_data.get('id')}: {str(e)}")
                self.stats['errors'] += 1

    def load_player_passes(self, player, passes_data):
        """Load pass data for a player"""
        for pass_data in passes_data:
            try:
                # Get or create game
                game = Game.objects.filter(game_id=pass_data.get('game_id')).first()
                if not game:
                    game, _ = Game.objects.get_or_create(
                        game_id=pass_data.get('game_id', 0),
                        defaults={
                            'game_date': timezone.now(),
                            'home_team_id': 1,
                            'away_team_id': 2,
                            'season': '2023-24',
                            'game_type': 'practice'
                        }
                    )

                # Check if pass already exists
                pass_obj, created = Pass.objects.get_or_create(
                    pass_id=pass_data.get('id'),
                    defaults={
                        'player': player,
                        'game': game,
                        'action_type': pass_data.get('action_type', 'unknown'),
                        'ball_start_loc_x': pass_data.get('ball_start_loc_x', 0),
                        'ball_start_loc_y': pass_data.get('ball_start_loc_y', 0),
                        'ball_end_loc_x': pass_data.get('ball_end_loc_x', 0),
                        'ball_end_loc_y': pass_data.get('ball_end_loc_y', 0),
                        'completed_pass': pass_data.get('completed_pass', True),
                        'potential_assist': pass_data.get('potential_assist', False),
                        'turnover': pass_data.get('turnover', False),
                        'quarter': pass_data.get('quarter'),
                        'time_remaining': pass_data.get('time_remaining')
                    }
                )

                if created:
                    self.stats['passes_loaded'] += 1

            except Exception as e:
                logger.error(f"Error loading pass {pass_data.get('id')}: {str(e)}")
                self.stats['errors'] += 1

    def load_player_turnovers(self, player, turnovers_data):
        """Load turnover data for a player"""
        for turnover_data in turnovers_data:
            try:
                # Get or create game
                game = Game.objects.filter(game_id=turnover_data.get('game_id')).first()
                if not game:
                    game, _ = Game.objects.get_or_create(
                        game_id=turnover_data.get('game_id', 0),
                        defaults={
                            'game_date': timezone.now(),
                            'home_team_id': 1,
                            'away_team_id': 2,
                            'season': '2023-24',
                            'game_type': 'practice'
                        }
                    )

                # Check if turnover already exists
                turnover, created = Turnover.objects.get_or_create(
                    turnover_id=turnover_data.get('id'),
                    defaults={
                        'player': player,
                        'game': game,
                        'action_type': turnover_data.get('action_type', 'unknown'),
                        'tov_loc_x': turnover_data.get('tov_loc_x', 0),
                        'tov_loc_y': turnover_data.get('tov_loc_y', 0),
                        'turnover_type': turnover_data.get('turnover_type'),
                        'quarter': turnover_data.get('quarter'),
                        'time_remaining': turnover_data.get('time_remaining')
                    }
                )

                if created:
                    self.stats['turnovers_loaded'] += 1

            except Exception as e:
                logger.error(f"Error loading turnover {turnover_data.get('id')}: {str(e)}")
                self.stats['errors'] += 1

    def calculate_game_stats(self):
        """Calculate aggregated game stats for all players"""
        logger.info("Calculating player game statistics...")

        players = Player.objects.all()
        games = Game.objects.all()

        for player in players:
            for game in games:
                # Check if player has any activity in this game
                has_activity = (
                    Shot.objects.filter(player=player, game=game).exists() or
                    Pass.objects.filter(player=player, game=game).exists() or
                    Turnover.objects.filter(player=player, game=game).exists()
                )

                if has_activity:
                    stats, created = PlayerGameStats.objects.get_or_create(
                        player=player,
                        game=game
                    )
                    stats.calculate_stats()
                    logger.debug(f"Calculated stats for {player.name} in game {game.game_id}")

    def print_summary(self):
        """Print summary of loaded data"""
        logger.info("\n" + "="*50)
        logger.info("DATA LOADING SUMMARY")
        logger.info("="*50)
        logger.info(f"Teams loaded:     {self.stats['teams_loaded']}")
        logger.info(f"Players loaded:   {self.stats['players_loaded']}")
        logger.info(f"Games loaded:     {self.stats['games_loaded']}")
        logger.info(f"Shots loaded:     {self.stats['shots_loaded']}")
        logger.info(f"Passes loaded:    {self.stats['passes_loaded']}")
        logger.info(f"Turnovers loaded: {self.stats['turnovers_loaded']}")
        logger.info(f"Errors:           {self.stats['errors']}")
        logger.info("="*50)

        # Print database totals
        logger.info("\nDatabase Totals:")
        logger.info(f"Total Teams:     {Team.objects.count()}")
        logger.info(f"Total Players:   {Player.objects.count()}")
        logger.info(f"Total Games:     {Game.objects.count()}")
        logger.info(f"Total Shots:     {Shot.objects.count()}")
        logger.info(f"Total Passes:    {Pass.objects.count()}")
        logger.info(f"Total Turnovers: {Turnover.objects.count()}")
        logger.info(f"Total Game Stats: {PlayerGameStats.objects.count()}")


def main():
    """Main entry point"""
    loader = NBADataLoader()
    loader.load_all()


if __name__ == '__main__':
    main()