/**
 * TypeScript Interfaces for NBA Player Summary Data
 * Comprehensive type definitions for the player statistics API response
 */

// Coordinate type for shot and turnover locations
export type Coordinate = [number, number]; // [x, y] in feet from basket center

// Shot data interface
export interface Shot {
  loc: Coordinate;
  points: number;
  shotDistance?: number;
  shotAngle?: number;
  foulDrawn?: boolean;
  gameId?: number;
}

// Pass data interface
export interface Pass {
  startLoc: Coordinate;
  endLoc: Coordinate;
  isCompleted: boolean;
  isPotentialAssist: boolean;
  isTurnover: boolean;
  passDistance?: number;
  gameId?: number;
}

// Turnover data interface
export interface Turnover {
  loc: Coordinate;
  turnoverType?: string;
  gameId?: number;
}

// Action type statistics interface
export interface ActionTypeStats {
  totalShotAttempts: number;
  totalPoints: number;
  totalPasses: number;
  totalPotentialAssists: number;
  totalTurnovers: number;
  totalPassingTurnovers: number;
  shots: Shot[];
  passes: Pass[];
  turnovers: Turnover[];
  fieldGoalPercentage?: number;
  assistToTurnoverRatio?: number;
}

// Hot zone interface for court areas
export interface HotZone {
  zone: string;
  shotsMade: number;
  shotsAttempted: number;
  percentage: number;
  rating: 'hot' | 'warm' | 'cold';
}

// Clutch statistics interface
export interface ClutchStats {
  clutchShootingPercentage: number;
  clutchAssists: number;
  clutchTurnovers: number;
}

// Advanced metrics interface
export interface AdvancedMetrics {
  trueShootingPercentage: number;
  playerEfficiencyRating: number;
  usageRate: number;
  pointsPerShot: number;
  assistToTurnoverRatio: number | 'Infinity';
  hotZones: HotZone[];
  clutchStats: ClutchStats;
}

// Player ranking interface
export interface PlayerRanks {
  totalShotAttemptsRank: number;
  totalPointsRank: number;
  totalPassesRank: number;
  totalPotentialAssistsRank: number;
  totalTurnoversRank: number;
  totalPassingTurnoversRank: number;
  pickAndRollCountRank: number;
  isolationCountRank: number;
  postUpCountRank: number;
  offBallScreenCountRank: number;
  percentileRanks?: PercentileRanks;
}

// Percentile rankings interface
export interface PercentileRanks {
  totalShotAttemptsPercentile?: number;
  totalPointsPercentile?: number;
  totalPassesPercentile?: number;
  totalPotentialAssistsPercentile?: number;
  totalTurnoversPercentile?: number;
  totalPassingTurnoversPercentile?: number;
  pickAndRollCountPercentile?: number;
  isolationCountPercentile?: number;
  postUpCountPercentile?: number;
  offBallScreenCountPercentile?: number;
  [key: string]: number | undefined;
}

// Main player summary interface
export interface PlayerSummary {
  // Basic info
  name: string;
  playerID: number;
  teamName?: string;
  teamID?: number;
  position?: string;
  jerseyNumber?: number;

  // Aggregate statistics
  totalShotAttempts: number;
  totalPoints: number;
  totalPasses: number;
  totalPotentialAssists: number;
  totalTurnovers: number;
  totalPassingTurnovers: number;

  // Shooting percentages
  fieldGoalPercentage?: number;
  effectiveFieldGoalPercentage?: number;
  passCompletionRate?: number;

  // Action type counts
  pickAndRollCount: number;
  isolationCount: number;
  postUpCount: number;
  offBallScreenCount: number;

  // Detailed action type data
  pickAndRoll: ActionTypeStats;
  isolation: ActionTypeStats;
  postUp: ActionTypeStats;
  offBallScreen: ActionTypeStats;

  // Advanced metrics
  advancedMetrics?: AdvancedMetrics;
}

// API response wrapper interface
export interface PlayerSummaryResponse {
  apiResponse: PlayerSummary;
  ranks?: PlayerRanks;
}

// Player comparison interface
export interface PlayerComparison {
  players: Array<{
    summary: PlayerSummary;
    ranks: PlayerRanks;
  }>;
}

// Filter options for the UI
export interface FilterOptions {
  actionTypes: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  minShotDistance?: number;
  maxShotDistance?: number;
  showMadeShots: boolean;
  showMissedShots: boolean;
}

// Court zone definitions for visualization
export interface CourtZone {
  name: string;
  bounds: {
    x: [number, number];
    y: [number, number];
  };
  color?: string;
  opacity?: number;
}

// Chart data interface for visualizations
export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }>;
}

// Stat comparison for multiple players
export interface StatComparison {
  statName: string;
  players: Array<{
    playerName: string;
    value: number;
    rank: number;
    percentile?: number;
  }>;
}

// Shot chart configuration
export interface ShotChartConfig {
  width: number;
  height: number;
  courtWidth: number;  // in feet
  courtHeight: number; // in feet
  scale: number;
  showZones: boolean;
  showHeatmap: boolean;
  animationDuration: number;
}

// Export all interfaces for easy import
export * from './player-summary.interfaces';