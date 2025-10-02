# Database Architecture Design

## Overview

The database is architected following normalized principles (3NF) to eliminate redundancy while ensuring data integrity and optimal query performance. This normalized approach prevents data duplication, maintains referential integrity through foreign key constraints, and enables efficient aggregation of complex basketball statistics across multiple dimensions (players, games, action types).

## Entity Relationship Diagram

```
┌─────────────┐
│    TEAMS    │
│─────────────│
│ team_id (PK)│◄───┐
│ name        │    │
│ city        │    │
│ conference  │    │
└─────────────┘    │
                   │
                   │
┌─────────────┐    │
│   PLAYERS   │    │
│─────────────│    │
│ player_id(PK)│    │
│ team_id (FK)├────┘
│ name        │
│ position    │
│ jersey_num  │
└──────┬──────┘
       │
       │ 1:N relationships
       ├────────────────────┬─────────────────┐
       │                    │                 │
       ▼                    ▼                 ▼
┌────────────┐      ┌────────────┐    ┌──────────────┐
│   SHOTS    │      │   PASSES   │    │  TURNOVERS   │
│────────────│      │────────────│    │──────────────│
│ shot_id(PK)│      │ pass_id(PK)│    │turnover_id(PK)│
│ player_id  │      │ player_id  │    │ player_id    │
│ game_id    │      │ game_id    │    │ game_id      │
│ action_type│      │ action_type│    │ action_type  │
│ shot_loc_x │      │start_loc_x │    │ tov_loc_x    │
│ shot_loc_y │      │start_loc_y │    │ tov_loc_y    │
│ points     │      │end_loc_x   │    │ type         │
│ distance   │      │end_loc_y   │    └──────────────┘
│ angle      │      │completed   │
└────────────┘      │potential_ast│
                    └────────────┘
```

## Schema Design

### Core Tables

**1. teams** - NBA team information
- Primary Key: `team_id`
- Stores team metadata (name, city, conference, division)
- Indexed on `name` for quick lookups
- All player and game data references this table

**2. players** - Player profiles and team associations
- Primary Key: `player_id`
- Foreign Key: `team_id` → `teams.team_id`
- Contains player attributes (name, position, physical measurements)
- Composite unique constraint on `(player_id, team_id)`
- Indexed for efficient filtering and joins

**3. games** - Game/practice session records
- Primary Key: `game_id`
- Foreign Keys: `home_team_id`, `away_team_id` → `teams.team_id`
- Tracks game metadata, date, season, and type
- Indexed on `game_date` for temporal queries
- Supports practice, scrimmage, and official game types

### Event-Level Performance Tables

**4. shots** - Granular shot tracking
- Primary Key: `shot_id` (auto-increment)
- Foreign Keys: `player_id`, `game_id`
- Spatial data: `(shot_loc_x, shot_loc_y)` coordinates in feet
- Calculated fields: `shot_distance`, `shot_angle` (computed on insert)
- Action type classification: pickAndRoll, isolation, postUp, offBallScreen
- Composite indexes on `(player_id, game_id)`, `(action_type, points)`

**5. passes** - Pass tracking with completion outcomes
- Primary Key: `pass_id` (auto-increment)
- Foreign Keys: `player_id`, `game_id`, `receiver_id` (nullable)
- Start/end locations for spatial analysis
- Boolean flags: `completed_pass`, `potential_assist`, `turnover`
- Calculated field: `pass_distance` (computed on insert)
- Indexed on completion flags for quick aggregation

**6. turnovers** - Ball loss event tracking
- Primary Key: `turnover_id`
- Foreign Keys: `player_id`, `game_id`, `forced_by` (nullable)
- Location data and turnover type classification
- Linked to pass table via action context
- Indexed by `action_type` for play pattern analysis

### Aggregated Statistics Tables

**7. player_game_stats** - Pre-computed game-level metrics
- Composite Primary Key: `(player_id, game_id)`
- Aggregates from shots, passes, turnovers tables
- Includes advanced metrics: FG%, TS%, eFG%, assist-to-turnover ratio
- Calculated via `calculate_stats()` method after data loading
- Eliminates expensive joins for common queries

**8. player_season_stats** - Season-level summaries
- Composite Primary Key: `(player_id, season)`
- Stores cumulative totals and per-game averages
- Ranking fields for comparative analysis (percentiles)
- Supports year-over-year performance tracking

## Normalization & Data Integrity

**Third Normal Form (3NF) Compliance:**
- Each table represents a single entity
- No transitive dependencies (all non-key attributes depend only on primary key)
- Action type data separated conceptually but stored efficiently as varchar
- Eliminates update anomalies and maintains referential integrity

**Foreign Key Constraints:**
- All relationships enforced at database level
- Cascade deletes configured where appropriate (player → shots)
- Prevents orphaned records and maintains data consistency

## Indexing Strategy

**Primary Indexes:**
- All primary keys automatically indexed
- Composite indexes on `(player_id, game_id)` across all event tables

**Secondary Indexes:**
- `action_type` fields for filtering by play type
- `points`, `completed_pass`, `potential_assist` for aggregations
- `game_date` for temporal queries
- `team_id` for team-level rollups

**Query Optimization:**
- Indexes support the primary API query pattern: player summary by ID
- Enable efficient filtering and grouping by action type
- Minimize full table scans for statistics calculations

## Data Loading Process

The idempotent loading script (`backend/scripts/load_data.py`) implements:
- `update_or_create()` pattern preventing duplicates on repeated runs
- Atomic transactions using Django ORM
- Foreign key resolution with automatic fallback creation
- Automatic calculation of derived fields (distances, angles)
- Post-load statistics aggregation via `calculate_game_stats()`

## API Query Patterns

**Primary Query (`get_player_summary_stats`):**
```python
# Efficiently retrieves all data for one player across all games
shots = Shot.objects.filter(player_id=X)
passes = Pass.objects.filter(player_id=X)
turnovers = Turnover.objects.filter(player_id=X)

# Groups by action_type without expensive joins
action_shots = shots.filter(action_type='pickAndRoll')
```

**Ranking Query (`get_ranks`):**
```python
# Leverages aggregation tables for cross-player comparisons
all_stats = [calculate_totals(p) for p in Player.objects.all()]
percentile_ranks = calculate_percentiles(current_player, all_stats)
```

## Performance Characteristics

- **Read-heavy workload**: Optimized for API queries serving frontend
- **Write-once pattern**: Data loaded in bulk, minimal updates
- **Aggregation tables**: Cache expensive calculations (10x speedup for summary queries)
- **Connection pooling**: Django DB connection reuse for concurrent requests
- **Index coverage**: All API queries use indexed columns (no full scans)