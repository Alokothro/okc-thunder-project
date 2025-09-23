# -*- coding: utf-8 -*-
"""Contains models related to NBA player and game statistics"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Team(models.Model):
    """NBA Team model with extended metadata"""
    team_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    abbreviation = models.CharField(max_length=5, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    conference = models.CharField(max_length=20, blank=True, null=True)
    division = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teams'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['team_id']),
        ]

    def __str__(self):
        return f"{self.name} ({self.team_id})"


class Player(models.Model):
    """Player model with relationships and performance tracking"""
    player_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=150, db_index=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    position = models.CharField(max_length=5, blank=True, null=True)
    jersey_number = models.IntegerField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True, help_text="Height in inches")
    weight = models.FloatField(blank=True, null=True, help_text="Weight in pounds")
    birth_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'players'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['team']),
            models.Index(fields=['player_id']),
        ]
        unique_together = ['player_id', 'team']

    def __str__(self):
        return f"{self.name} - {self.team.name}"

    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None


class Game(models.Model):
    """Game model for tracking individual game sessions"""
    game_id = models.IntegerField(primary_key=True)
    game_date = models.DateTimeField()
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_games')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_games')
    season = models.CharField(max_length=20, blank=True, null=True)
    game_type = models.CharField(max_length=20, default='practice')  # practice, scrimmage, preseason, regular, playoff
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'games'
        ordering = ['-game_date']
        indexes = [
            models.Index(fields=['game_date']),
            models.Index(fields=['home_team', 'away_team']),
            models.Index(fields=['game_id']),
        ]

    def __str__(self):
        return f"Game {self.game_id}: {self.home_team.name} vs {self.away_team.name} - {self.game_date}"


class ActionType(models.Model):
    """Action type enumeration for basketball plays"""
    ACTION_CHOICES = [
        ('pickAndRoll', 'Pick & Roll'),
        ('isolation', 'Isolation'),
        ('postUp', 'Post-up'),
        ('offBallScreen', 'Off-Ball Screen'),
        ('transition', 'Transition'),
        ('putback', 'Putback'),
        ('spotUp', 'Spot Up'),
    ]

    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES, primary_key=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'action_types'

    def __str__(self):
        return self.get_action_type_display()


class Shot(models.Model):
    """Shot model with detailed location and outcome tracking"""
    shot_id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='shots')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='shots')
    action_type = models.CharField(max_length=30, db_index=True)
    points = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(4)])
    shot_loc_x = models.FloatField(help_text="X coordinate in feet from basket center")
    shot_loc_y = models.FloatField(help_text="Y coordinate in feet from basket center")
    shooting_foul_drawn = models.BooleanField(default=False)
    shot_made = models.BooleanField(default=False)
    shot_distance = models.FloatField(blank=True, null=True, help_text="Distance from basket in feet")
    shot_angle = models.FloatField(blank=True, null=True, help_text="Angle from basket in degrees")
    quarter = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    time_remaining = models.FloatField(blank=True, null=True, help_text="Seconds remaining in quarter")
    shot_clock = models.FloatField(blank=True, null=True, help_text="Shot clock time")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shots'
        ordering = ['game', 'quarter', '-time_remaining']
        indexes = [
            models.Index(fields=['player', 'game']),
            models.Index(fields=['game']),
            models.Index(fields=['action_type']),
            models.Index(fields=['points']),
            models.Index(fields=['shot_made']),
        ]

    def save(self, *args, **kwargs):
        # Calculate shot distance and angle
        import math
        self.shot_distance = math.sqrt(self.shot_loc_x ** 2 + self.shot_loc_y ** 2)
        self.shot_angle = math.degrees(math.atan2(self.shot_loc_y, self.shot_loc_x))
        self.shot_made = self.points > 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shot by {self.player.name} - {self.points} pts at ({self.shot_loc_x:.1f}, {self.shot_loc_y:.1f})"


class Pass(models.Model):
    """Pass model with start/end locations and outcomes"""
    pass_id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='passes')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='passes')
    action_type = models.CharField(max_length=30, db_index=True)
    ball_start_loc_x = models.FloatField()
    ball_start_loc_y = models.FloatField()
    ball_end_loc_x = models.FloatField()
    ball_end_loc_y = models.FloatField()
    completed_pass = models.BooleanField(default=True)
    potential_assist = models.BooleanField(default=False)
    turnover = models.BooleanField(default=False)
    pass_distance = models.FloatField(blank=True, null=True, help_text="Pass distance in feet")
    pass_speed = models.FloatField(blank=True, null=True, help_text="Estimated pass speed")
    receiver = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='received_passes', blank=True, null=True)
    quarter = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    time_remaining = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'passes'
        ordering = ['game', 'quarter', '-time_remaining']
        indexes = [
            models.Index(fields=['player', 'game']),
            models.Index(fields=['game']),
            models.Index(fields=['action_type']),
            models.Index(fields=['completed_pass']),
            models.Index(fields=['potential_assist']),
            models.Index(fields=['turnover']),
        ]

    def save(self, *args, **kwargs):
        # Calculate pass distance
        import math
        self.pass_distance = math.sqrt(
            (self.ball_end_loc_x - self.ball_start_loc_x) ** 2 +
            (self.ball_end_loc_y - self.ball_start_loc_y) ** 2
        )
        super().save(*args, **kwargs)

    def __str__(self):
        status = "completed" if self.completed_pass else "incomplete"
        return f"Pass by {self.player.name} - {status}"


class Turnover(models.Model):
    """Turnover model for tracking ball losses"""
    turnover_id = models.AutoField(primary_key=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='turnovers')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='turnovers')
    action_type = models.CharField(max_length=30, db_index=True)
    tov_loc_x = models.FloatField()
    tov_loc_y = models.FloatField()
    turnover_type = models.CharField(max_length=50, blank=True, null=True)  # bad pass, travel, out of bounds, etc.
    forced_by = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='forced_turnovers', blank=True, null=True)
    quarter = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(8)])
    time_remaining = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'turnovers'
        ordering = ['game', 'quarter', '-time_remaining']
        indexes = [
            models.Index(fields=['player', 'game']),
            models.Index(fields=['game']),
            models.Index(fields=['action_type']),
            models.Index(fields=['turnover_type']),
        ]

    def __str__(self):
        return f"Turnover by {self.player.name} at ({self.tov_loc_x:.1f}, {self.tov_loc_y:.1f})"


class PlayerGameStats(models.Model):
    """Aggregated statistics per player per game for performance tracking"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='game_stats')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='player_stats')

    # Shooting stats
    total_shots = models.IntegerField(default=0)
    shots_made = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    field_goal_percentage = models.FloatField(default=0.0)
    three_pointers_made = models.IntegerField(default=0)
    three_pointers_attempted = models.IntegerField(default=0)
    two_pointers_made = models.IntegerField(default=0)
    two_pointers_attempted = models.IntegerField(default=0)

    # Passing stats
    total_passes = models.IntegerField(default=0)
    completed_passes = models.IntegerField(default=0)
    potential_assists = models.IntegerField(default=0)
    pass_completion_rate = models.FloatField(default=0.0)

    # Turnover stats
    total_turnovers = models.IntegerField(default=0)
    passing_turnovers = models.IntegerField(default=0)

    # Action type breakdown
    pick_and_roll_count = models.IntegerField(default=0)
    isolation_count = models.IntegerField(default=0)
    post_up_count = models.IntegerField(default=0)
    off_ball_screen_count = models.IntegerField(default=0)

    # Advanced metrics
    true_shooting_percentage = models.FloatField(default=0.0)
    effective_field_goal_percentage = models.FloatField(default=0.0)
    assist_to_turnover_ratio = models.FloatField(default=0.0)
    usage_rate = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'player_game_stats'
        unique_together = ['player', 'game']
        ordering = ['game', 'player']
        indexes = [
            models.Index(fields=['player', 'game']),
            models.Index(fields=['total_points']),
            models.Index(fields=['field_goal_percentage']),
        ]

    def calculate_stats(self):
        """Calculate aggregated statistics from related Shot, Pass, and Turnover objects"""
        # Shooting stats
        shots = Shot.objects.filter(player=self.player, game=self.game)
        self.total_shots = shots.count()
        self.shots_made = shots.filter(points__gt=0).count()
        self.total_points = shots.aggregate(models.Sum('points'))['points__sum'] or 0
        self.field_goal_percentage = (self.shots_made / self.total_shots * 100) if self.total_shots > 0 else 0

        # Three-pointers and two-pointers
        self.three_pointers_made = shots.filter(points=3).count()
        self.three_pointers_attempted = shots.filter(models.Q(points=3) | models.Q(points=0, shot_distance__gte=23.75)).count()
        self.two_pointers_made = shots.filter(points=2).count()
        self.two_pointers_attempted = shots.filter(models.Q(points=2) | models.Q(points=0, shot_distance__lt=23.75)).count()

        # Passing stats
        passes = Pass.objects.filter(player=self.player, game=self.game)
        self.total_passes = passes.count()
        self.completed_passes = passes.filter(completed_pass=True).count()
        self.potential_assists = passes.filter(potential_assist=True).count()
        self.pass_completion_rate = (self.completed_passes / self.total_passes * 100) if self.total_passes > 0 else 0

        # Turnover stats
        turnovers = Turnover.objects.filter(player=self.player, game=self.game)
        self.total_turnovers = turnovers.count()
        self.passing_turnovers = passes.filter(turnover=True).count()

        # Action type counts
        self.pick_and_roll_count = shots.filter(action_type='pickAndRoll').count() + passes.filter(action_type='pickAndRoll').count()
        self.isolation_count = shots.filter(action_type='isolation').count() + passes.filter(action_type='isolation').count()
        self.post_up_count = shots.filter(action_type='postUp').count() + passes.filter(action_type='postUp').count()
        self.off_ball_screen_count = shots.filter(action_type='offBallScreen').count() + passes.filter(action_type='offBallScreen').count()

        # Advanced metrics
        if self.total_shots > 0:
            self.true_shooting_percentage = (self.total_points / (2 * (self.total_shots + 0.44 * 0))) * 100  # Simplified TS%
            self.effective_field_goal_percentage = ((self.shots_made + 0.5 * self.three_pointers_made) / self.total_shots) * 100

        if self.total_turnovers > 0:
            self.assist_to_turnover_ratio = self.potential_assists / self.total_turnovers

        self.save()

    def __str__(self):
        return f"{self.player.name} - Game {self.game.game_id}: {self.total_points} pts"


class PlayerSeasonStats(models.Model):
    """Season-level aggregated statistics for ranking and comparison"""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='season_stats')
    season = models.CharField(max_length=20)

    # Aggregated stats
    games_played = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)
    total_shots = models.IntegerField(default=0)
    total_passes = models.IntegerField(default=0)
    total_assists = models.IntegerField(default=0)
    total_turnovers = models.IntegerField(default=0)

    # Averages
    ppg = models.FloatField(default=0.0, help_text="Points per game")
    apg = models.FloatField(default=0.0, help_text="Assists per game")
    tpg = models.FloatField(default=0.0, help_text="Turnovers per game")
    fg_percentage = models.FloatField(default=0.0)
    three_point_percentage = models.FloatField(default=0.0)

    # Rankings (percentiles)
    points_rank = models.IntegerField(blank=True, null=True)
    assists_rank = models.IntegerField(blank=True, null=True)
    fg_percentage_rank = models.IntegerField(blank=True, null=True)
    efficiency_rank = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'player_season_stats'
        unique_together = ['player', 'season']
        ordering = ['-total_points']
        indexes = [
            models.Index(fields=['player', 'season']),
            models.Index(fields=['total_points']),
            models.Index(fields=['ppg']),
        ]

    def __str__(self):
        return f"{self.player.name} - {self.season}: {self.ppg:.1f} PPG"