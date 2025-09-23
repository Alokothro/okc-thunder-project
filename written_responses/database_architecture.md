# Database Architecture Design

## Overview

The database is designed following normalized principles (3NF) to minimize redundancy and ensure data integrity. The architecture supports efficient querying of player statistics while maintaining flexibility for future enhancements.

## Schema Design

### Core Tables

1. **teams** - NBA team information
   - Primary Key: team_id
   - Stores team metadata (name, city, conference, division)
   - Indexed on name for quick lookups

2. **players** - Player profiles and associations
   - Primary Key: player_id
   - Foreign Key: team_id references teams
   - Contains player attributes (name, position, physical stats)
   - Composite index on (player_id, team_id) for efficient joins

3. **games** - Game/practice session records
   - Primary Key: game_id
   - Foreign Keys: home_team_id, away_team_id reference teams
   - Tracks game metadata and type (practice, scrimmage, regular)
   - Indexed on game_date for temporal queries

### Performance Data Tables

4. **shots** - Detailed shot tracking
   - Primary Key: shot_id (auto-increment)
   - Foreign Keys: player_id, game_id
   - Stores location (x,y coordinates), points, action type
   - Calculated fields: shot_distance, shot_angle
   - Multiple indexes for filtering by player, game, and outcome

5. **passes** - Pass tracking with spatial data
   - Primary Key: pass_id (auto-increment)
   - Foreign Keys: player_id, game_id, receiver_id
   - Contains start/end locations, completion status, assist potential
   - Calculated field: pass_distance
   - Indexed on completion and assist flags

6. **turnovers** - Ball loss events
   - Primary Key: turnover_id
   - Foreign Keys: player_id, game_id, forced_by_player_id
   - Location-based with turnover type classification
   - Indexed by action_type for analysis

### Aggregated Statistics Tables

7. **player_game_stats** - Pre-calculated game-level statistics
   - Composite Key: (player_id, game_id)
   - Aggregates shots, passes, turnovers per game
   - Includes calculated metrics (FG%, TS%, usage rate)
   - Optimizes read performance for common queries

8. **player_season_stats** - Season-level aggregations
   - Composite Key: (player_id, season)
   - Stores cumulative stats and averages
   - Includes ranking fields for comparative analysis

## Key Design Decisions

1. **Normalization**: Eliminated redundancy by separating entities (teams, players, games) into distinct tables

2. **Calculated Fields**: Pre-compute expensive calculations (distances, angles) during inserts rather than at query time

3. **Indexing Strategy**: Created indexes on foreign keys and commonly filtered columns (action_type, points, dates)

4. **Aggregation Tables**: Materialized views for frequently accessed summaries reduce join complexity

5. **Flexible Action Types**: Used string field instead of enum to accommodate future play types without schema changes

## Performance Optimizations

- Composite indexes on (player_id, game_id) for efficient filtering
- Partial indexes on boolean fields (completed_pass, shooting_foul_drawn)
- Table partitioning considered for shots/passes tables as data grows
- Connection pooling configured in Django for concurrent access

## Scalability Considerations

The schema supports horizontal partitioning by date/season for historical data archival. Read replicas can be added for analytics workloads without impacting transactional performance.