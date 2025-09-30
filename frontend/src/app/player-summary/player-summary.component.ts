import {
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  ViewEncapsulation,
  ElementRef,
  ViewChild,
  AfterViewInit
} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {untilDestroyed, UntilDestroy} from '@ngneat/until-destroy';
import {PlayersService} from '../_services/players.service';
import {
  PlayerSummary,
  PlayerSummaryResponse,
  PlayerRanks,
  Shot,
  Pass,
  Turnover,
  ActionTypeStats,
  FilterOptions,
  CourtZone,
  ChartData
} from './player-summary.interfaces';
import * as d3 from 'd3';
import { Chart, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

@UntilDestroy()
@Component({
  selector: 'player-summary-component',
  templateUrl: './player-summary.component.html',
  styleUrls: ['./player-summary.component.scss'],
  encapsulation: ViewEncapsulation.None,
})
export class PlayerSummaryComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('courtCanvas', { static: false }) courtCanvas: ElementRef<HTMLCanvasElement>;
  @ViewChild('statsChart', { static: false }) statsChart: ElementRef<HTMLCanvasElement>;

  // Player data
  playerSummary: PlayerSummary | null = null;
  playerRanks: PlayerRanks | null = null;

  // UI state
  selectedPlayerId = 1; // Default to Player 1
  selectedActionType = 'all';
  loading = false;
  error: string | null = null;

  // Filter options
  filterOptions: FilterOptions = {
    actionTypes: ['pickAndRoll', 'isolation', 'postUp', 'offBallScreen'],
    showMadeShots: true,
    showMissedShots: true,
    minShotDistance: 0,
    maxShotDistance: 50
  };

  // Court dimensions (in pixels)
  courtWidth = 500;
  courtHeight = 470;
  courtScale = 10; // pixels per foot

  // Chart instances
  shotChart: any;
  statsBarChart: Chart | null = null;

  // Court zones for visualization
  courtZones: CourtZone[] = [
    {
      name: 'Restricted Area',
      bounds: { x: [-80, 80], y: [0, 80] },
      color: '#ff6b6b',
      opacity: 0.3
    },
    {
      name: 'Paint',
      bounds: { x: [-80, 80], y: [80, 190] },
      color: '#4ecdc4',
      opacity: 0.3
    },
    {
      name: 'Mid-Range',
      bounds: { x: [-220, 220], y: [80, 240] },
      color: '#45b7d1',
      opacity: 0.3
    },
    {
      name: 'Three-Point',
      bounds: { x: [-250, 250], y: [240, 470] },
      color: '#96ceb4',
      opacity: 0.3
    }
  ];

  constructor(
    protected activatedRoute: ActivatedRoute,
    protected cdr: ChangeDetectorRef,
    protected playersService: PlayersService,
  ) {}

  ngOnInit(): void {
    this.loadPlayerData();
  }

  ngAfterViewInit(): void {
    // Visualizations will be drawn after data loads in loadPlayerData()
  }

  ngOnDestroy(): void {
    if (this.statsBarChart) {
      this.statsBarChart.destroy();
    }
  }

  /**
   * Load player data from API
   */
  loadPlayerData(): void {
    this.loading = true;
    this.error = null;

    // Get player ID from route or input
    const playerId = this.selectedPlayerId;

    this.playersService.getPlayerSummary(playerId)
      .pipe(untilDestroyed(this))
      .subscribe({
        next: (response: PlayerSummaryResponse) => {
          console.log('Player Data:', response);
          this.playerSummary = response.apiResponse;
          this.playerRanks = response.ranks || null;
          this.loading = false;

          // Trigger change detection first
          this.cdr.detectChanges();

          // Refresh visualizations after DOM update
          setTimeout(() => {
            if (this.courtCanvas && this.courtCanvas.nativeElement) {
              this.drawCourt();
            }
            if (this.statsChart && this.statsChart.nativeElement) {
              this.createStatsChart();
            }
          }, 100);
        },
        error: (error) => {
          console.error('Error loading player data:', error);
          this.error = 'Failed to load player data';
          this.loading = false;
          this.cdr.detectChanges();
        }
      });
  }

  /**
   * Draw basketball court using D3.js
   */
  drawCourt(): void {
    if (!this.courtCanvas) return;

    const canvas = this.courtCanvas.nativeElement;
    const context = canvas.getContext('2d');
    if (!context) return;

    // Set canvas dimensions
    canvas.width = this.courtWidth;
    canvas.height = this.courtHeight;

    // Clear canvas
    context.clearRect(0, 0, canvas.width, canvas.height);

    // Draw court outline
    context.strokeStyle = '#000';
    context.lineWidth = 2;
    context.strokeRect(0, 0, this.courtWidth, this.courtHeight);

    // Draw paint/key
    const paintWidth = 160;
    const paintHeight = 190;
    const paintX = (this.courtWidth - paintWidth) / 2;

    context.strokeStyle = '#000';
    context.lineWidth = 2;
    context.strokeRect(paintX, 0, paintWidth, paintHeight);

    // Draw free throw circle
    const ftCircleRadius = 60;
    const ftCircleY = paintHeight;

    context.beginPath();
    context.arc(this.courtWidth / 2, ftCircleY, ftCircleRadius, 0, Math.PI * 2);
    context.stroke();

    // Draw restricted area
    const restrictedRadius = 40;

    context.beginPath();
    context.arc(this.courtWidth / 2, 50, restrictedRadius, 0, Math.PI, true);
    context.strokeStyle = '#ff0000';
    context.lineWidth = 2;
    context.stroke();

    // Draw three-point line
    const threePointRadius = 237.5; // 23.75 feet in pixels (scale 10)
    const threePointY = 50; // Basket position

    context.beginPath();
    context.arc(this.courtWidth / 2, threePointY, threePointRadius, 0.15 * Math.PI, 0.85 * Math.PI);
    context.strokeStyle = '#000';
    context.lineWidth = 2;
    context.stroke();

    // Draw corner three-point lines
    context.beginPath();
    context.moveTo(30, 0);
    context.lineTo(30, 90);
    context.moveTo(this.courtWidth - 30, 0);
    context.lineTo(this.courtWidth - 30, 90);
    context.stroke();

    // Draw basket
    const basketRadius = 9;
    context.beginPath();
    context.arc(this.courtWidth / 2, 50, basketRadius, 0, Math.PI * 2);
    context.fillStyle = '#ff7f00';
    context.fill();
    context.strokeStyle = '#000';
    context.lineWidth = 2;
    context.stroke();

    // Plot shots if data is available
    if (this.playerSummary) {
      this.plotShots();
    }
  }

  /**
   * Plot shots on the court
   */
  plotShots(): void {
    if (!this.courtCanvas || !this.playerSummary) return;

    const canvas = this.courtCanvas.nativeElement;
    const context = canvas.getContext('2d');
    if (!context) return;

    // Get shots based on selected action type
    let shots: Shot[] = [];

    if (this.selectedActionType === 'all') {
      shots = [
        ...this.playerSummary.pickAndRoll.shots,
        ...this.playerSummary.isolation.shots,
        ...this.playerSummary.postUp.shots,
        ...this.playerSummary.offBallScreen.shots
      ];
    } else {
      const actionData = this.playerSummary[this.selectedActionType] as ActionTypeStats;
      shots = actionData ? actionData.shots : [];
    }

    // Plot each shot
    shots.forEach(shot => {
      const x = this.courtWidth / 2 + (shot.loc[0] * this.courtScale);
      const y = 50 + (shot.loc[1] * this.courtScale);

      // Skip if filtering
      if (shot.points > 0 && !this.filterOptions.showMadeShots) return;
      if (shot.points === 0 && !this.filterOptions.showMissedShots) return;

      // Draw shot marker
      context.beginPath();
      context.arc(x, y, 5, 0, Math.PI * 2);

      // Color based on outcome
      if (shot.points === 0) {
        context.fillStyle = 'rgba(255, 0, 0, 0.6)'; // Red for miss
      } else if (shot.points === 2) {
        context.fillStyle = 'rgba(0, 255, 0, 0.6)'; // Green for 2-pointer
      } else if (shot.points === 3) {
        context.fillStyle = 'rgba(0, 100, 255, 0.6)'; // Blue for 3-pointer
      } else {
        context.fillStyle = 'rgba(255, 165, 0, 0.6)'; // Orange for other
      }

      context.fill();
      context.strokeStyle = '#000';
      context.lineWidth = 1;
      context.stroke();
    });

    // Draw heat map overlay if enabled
    if (this.playerSummary.advancedMetrics?.hotZones) {
      this.drawHeatMap();
    }
  }

  /**
   * Draw heat map overlay for hot zones
   */
  drawHeatMap(): void {
    if (!this.courtCanvas || !this.playerSummary?.advancedMetrics?.hotZones) return;

    const canvas = this.courtCanvas.nativeElement;
    const context = canvas.getContext('2d');
    if (!context) return;

    // Save current context state
    context.save();

    // Draw semi-transparent overlays for hot zones
    this.playerSummary.advancedMetrics.hotZones.forEach(zone => {
      if (zone.shotsAttempted === 0) return;

      // Determine color based on shooting percentage
      let color: string;
      if (zone.rating === 'hot') {
        color = 'rgba(255, 0, 0, 0.3)'; // Red for hot
      } else if (zone.rating === 'warm') {
        color = 'rgba(255, 165, 0, 0.3)'; // Orange for warm
      } else {
        color = 'rgba(0, 0, 255, 0.3)'; // Blue for cold
      }

      // Draw zone overlay (simplified rectangular zones)
      context.fillStyle = color;

      // Map zone names to court areas (simplified)
      if (zone.zone === 'Restricted Area') {
        context.fillRect(this.courtWidth/2 - 80, 10, 160, 80);
      } else if (zone.zone.includes('Corner 3')) {
        if (zone.zone.includes('Left')) {
          context.fillRect(0, 0, 90, 90);
        } else {
          context.fillRect(this.courtWidth - 90, 0, 90, 90);
        }
      }
    });

    // Restore context
    context.restore();
  }

  /**
   * Create stats comparison chart
   */
  createStatsChart(): void {
    if (!this.statsChart || !this.playerSummary) return;

    const canvas = this.statsChart.nativeElement;
    const context = canvas.getContext('2d');
    if (!context) return;

    // Destroy existing chart
    if (this.statsBarChart) {
      this.statsBarChart.destroy();
    }

    // Prepare chart data
    const chartData: ChartData = {
      labels: ['Points', 'Assists', 'FG%', 'Pass%', 'Turnovers'],
      datasets: [{
        label: this.playerSummary.name,
        data: [
          this.playerSummary.totalPoints,
          this.playerSummary.totalPotentialAssists,
          this.playerSummary.fieldGoalPercentage || 0,
          this.playerSummary.passCompletionRate || 0,
          this.playerSummary.totalTurnovers
        ],
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)'
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)'
        ],
        borderWidth: 2
      }]
    };

    // Create chart
    this.statsBarChart = new Chart(context, {
      type: 'bar',
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          title: {
            display: true,
            text: 'Player Statistics Overview'
          }
        },
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
  }

  /**
   * Handle action type filter change
   */
  onActionTypeChange(actionType: string): void {
    this.selectedActionType = actionType;
    this.drawCourt();
  }

  /**
   * Handle player ID change
   */
  onPlayerIdChange(playerId: number): void {
    this.selectedPlayerId = playerId;
    this.loadPlayerData();
  }


  /**
   * Get action type display name
   */
  getActionTypeDisplayName(actionType: string): string {
    const displayNames: { [key: string]: string } = {
      'pickAndRoll': 'Pick & Roll',
      'isolation': 'Isolation',
      'postUp': 'Post-Up',
      'offBallScreen': 'Off-Ball Screen'
    };
    return displayNames[actionType] || actionType;
  }

  /**
   * Get rank color class
   */
  getRankColorClass(rank: number): string {
    if (rank <= 3) return 'rank-excellent';
    if (rank <= 5) return 'rank-good';
    if (rank <= 7) return 'rank-average';
    return 'rank-below-average';
  }

  /**
   * Calculate shooting percentage for action type
   */
  getActionTypeShootingPercentage(actionType: string): number {
    if (!this.playerSummary) return 0;

    const actionData = this.playerSummary[actionType] as ActionTypeStats;
    if (!actionData || actionData.totalShotAttempts === 0) return 0;

    return actionData.fieldGoalPercentage || 0;
  }
}