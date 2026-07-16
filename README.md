> [!NOTE]
> **Archived**
>
> This project was completed as a technical assessment and is no longer actively maintained. The codebase is preserved as-is for reference.

# OKC Thunder Player Analytics Dashboard ⚡🏀

A full-stack NBA player performance tracking and visualization platform built with Django REST Framework, PostgreSQL, Angular, and D3.js. Features comprehensive player statistics, shot chart visualizations, and advanced basketball analytics.

**🎯 Live Demo:** https://frontend-production-214a.up.railway.app

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Django](https://img.shields.io/badge/Django-REST-green)
![Angular](https://img.shields.io/badge/Angular-12-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Railway](https://img.shields.io/badge/Deployed-Railway-purple)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Technology Stack](#-technology-stack)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
- [Installation & Setup](#-installation--setup)
- [API Documentation](#-api-documentation)
- [Database Design](#-database-design)
- [Deployment](#-deployment)

---

## 🎯 Project Overview

This is a production-ready NBA player analytics platform developed for the OKC Thunder internship technical assessment. The application analyzes player performance data from practice sessions, tracking shots, passes, and turnovers across different halfcourt action types (Pick & Roll, Isolation, Post-Up, Off-Ball Screen).

### Business Impact

- ✅ **Advanced Analytics**: True Shooting %, Player Efficiency Rating, Usage Rate
- ✅ **Interactive Visualizations**: D3.js shot charts with heat maps
- ✅ **Player Rankings**: Percentile-based performance comparisons
- ✅ **Action Filtering**: Dynamic filtering by play type
- ✅ **Responsive Design**: Optimized for desktop and mobile viewing

---

## 🛠 Technology Stack

### Backend Technologies

- **Python 3.10** - Core programming language
- **Django 4.2** - Web framework
- **Django REST Framework** - RESTful API development
- **PostgreSQL** - Production database (Railway)
- **SQLite** - Local development database
- **psycopg2** - PostgreSQL adapter
- **NumPy** - Numerical computations
- **SciPy** - Statistical analysis and percentile rankings

### Frontend Technologies

- **Angular 12** - Frontend framework
- **TypeScript 4.3** - Static typing
- **D3.js 7.8** - Shot chart visualizations
- **Chart.js 3.9** - Statistics charts
- **Angular Material 12** - UI components
- **RxJS 6.5** - Reactive programming
- **SCSS** - Advanced styling

### Database & Storage

- **PostgreSQL** - Normalized relational database
- **3NF Schema** - 8 tables with foreign key relationships
- **Indexed Queries** - Optimized for player lookups and aggregations

### Development Tools

- **Git/GitHub** - Version control
- **pyenv** - Python version management
- **npm** - Node package management
- **Railway CLI** - Deployment tooling

### Deployment & Infrastructure

- **Railway** - Cloud platform (Frontend, Backend, Database)
- **Gunicorn** - WSGI HTTP server
- **Nginx** - Reverse proxy (via Railway)
- **HTTPS/SSL** - Secure communication

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Angular Frontend                         │
│     TypeScript + D3.js + Chart.js + Material Design        │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API (JSON)
┌─────────────────────▼───────────────────────────────────────┐
│               Django REST Framework                         │
│  ┌──────────────┐ ┌──────────────┐ ┌───────────────────┐  │
│  │   API Views  │ │    Helpers   │ │   Data Models     │  │
│  │ (PlayerSummary)│ │ (Rankings)  │ │  (SQLAlchemy)    │  │
│  └──────────────┘ └──────────────┘ └───────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │ Django ORM
┌─────────────────────▼───────────────────────────────────────┐
│                PostgreSQL Database                          │
│   Teams | Players | Games | Shots | Passes | Turnovers    │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### Backend Features

✅ **Normalized Database** - 8 tables in 3NF with proper relationships
✅ **Idempotent Data Loading** - Repeatable script using `update_or_create()`
✅ **Player Summary API** - Comprehensive statistics by action type
✅ **Ranking System** - Percentile-based player comparisons
✅ **Advanced Metrics** - True Shooting %, PER, Usage Rate, Hot Zones
✅ **Spatial Data** - X/Y coordinates for shots, passes, turnovers
✅ **Action Classification** - Pick & Roll, Isolation, Post-Up, Off-Ball Screen

### Frontend Features

✅ **TypeScript Interfaces** - 222 lines of comprehensive type definitions
✅ **Shot Chart Visualization** - D3.js canvas rendering with court overlay
✅ **Action Type Filtering** - Dynamic card display for selected play types
✅ **Statistics Charts** - Chart.js bar charts for performance metrics
✅ **Heat Map Overlays** - Color-coded shooting zones by percentage
✅ **Responsive Design** - Mobile-optimized with Thunder blue theme
✅ **Real-time Updates** - RxJS observables for seamless data flow

### Analytics Features

✅ **Hot Zones** - Court areas with shooting percentage ratings
✅ **Clutch Stats** - Performance in pressure situations (placeholder)
✅ **Player Efficiency Rating** - Simplified PER calculation
✅ **Usage Rate** - Percentage of team possessions used
✅ **Assist-to-Turnover Ratio** - Playmaking efficiency metric

---

## 💻 Installation & Setup

### Prerequisites

- **Python 3.10+**
- **Node.js 16.x** (NOT 18+ or 22+ - Angular 12 compatibility)
- **PostgreSQL 14+**
- **nvm** (recommended for Node version management)

### Backend Setup

```bash
# Clone repository
git clone https://github.com/Alokothro/okc-thunder-project.git
cd okc-thunder-project

# Create PostgreSQL database
createuser okcapplicant --createdb
createdb okc
psql okc

# In psql terminal:
CREATE SCHEMA app;
ALTER USER okcapplicant WITH PASSWORD 'thunder';
GRANT ALL ON SCHEMA app TO okcapplicant;
\q

# Set up Python environment
cd backend
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Load data
python scripts/load_data.py

# Start backend server
python manage.py runserver
# Backend runs on http://localhost:8000
```

### Frontend Setup

```bash
# Install Node 16 (REQUIRED)
nvm install 16
nvm use 16
node --version  # Must show v16.x.x

# Navigate to frontend
cd frontend

# Install dependencies
npm install --force

# Start development server
npm start
# Frontend runs on http://localhost:4200
```

---

## 📡 API Documentation

### Player Summary Endpoint

```http
GET /api/v1/playerSummary/{playerID}
```

**Response Structure:**

```json
{
  "name": "Player Name",
  "playerID": 1,
  "teamName": "Team Name",
  "teamID": 1,
  "position": "PG",
  "jerseyNumber": 0,
  "totalShotAttempts": 13,
  "totalPoints": 14,
  "totalPasses": 10,
  "totalPotentialAssists": 3,
  "totalTurnovers": 1,
  "fieldGoalPercentage": 53.8,
  "effectiveFieldGoalPercentage": 53.8,
  "passCompletionRate": 100.0,
  "pickAndRollCount": 11,
  "isolationCount": 7,
  "postUpCount": 4,
  "offBallScreenCount": 1,
  "pickAndRoll": {
    "totalShotAttempts": 7,
    "totalPoints": 6,
    "shots": [
      {
        "loc": [-10.74, 2.0],
        "points": 2,
        "shotDistance": 10.92,
        "shotAngle": 169.5,
        "foulDrawn": false,
        "gameId": 7
      }
    ],
    "passes": [...],
    "turnovers": [...]
  },
  "advancedMetrics": {
    "trueShootingPercentage": 65.2,
    "playerEfficiencyRating": 18.5,
    "usageRate": 22.3,
    "hotZones": [...]
  },
  "totalShotAttemptsRank": 5,
  "totalPointsRank": 3,
  "percentileRanks": {
    "totalPointsPercentile": 85.0
  }
}
```

---

## 🗄 Database Design

### Entity Relationship Diagram

```
┌─────────────┐
│    TEAMS    │
│─────────────│
│ team_id (PK)│◄───┐
│ name        │    │
│ city        │    │
└─────────────┘    │
                   │
┌─────────────┐    │
│   PLAYERS   │    │
│─────────────│    │
│ player_id(PK)│    │
│ team_id (FK)├────┘
│ name        │
│ position    │
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
└────────────┘      │end_loc_y   │    └──────────────┘
                    └────────────┘
```

### Core Tables

- **teams** - NBA team metadata (10 teams)
- **players** - Player profiles and attributes (10 players)
- **games** - Practice/game sessions (39 games)
- **shots** - Shot attempts with location and outcome (192 shots)
- **passes** - Pass data with completion status (165 passes)
- **turnovers** - Ball loss events (14 turnovers)
- **player_game_stats** - Aggregated per-game statistics
- **player_season_stats** - Season-level summaries

---

## 🚀 Deployment

### Production URLs

- **Frontend:** https://frontend-production-214a.up.railway.app
- **Backend:** https://backend-production-af17.up.railway.app

### Railway Deployment Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Railway DB     │────▶│  Backend Service│────▶│ Frontend Service│
│  PostgreSQL     │     │  Django + Gunicorn│   │  Angular + Nginx│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Environment Variables

**Backend:**
```bash
DATABASE_URL=postgresql://...
DJANGO_SETTINGS_MODULE=app.settings
```

**Frontend:**
```bash
BACKEND_PUBLIC_DOMAIN=https://backend-production-af17.up.railway.app
```

---

## 👨‍💻 Developer

**Alok Patel** - Computer Science Student | Software Engineering

📧 Email: alokothro@gmail.com
🔗 GitHub: [@Alokothro](https://github.com/Alokothro)
💼 LinkedIn: [Connect with me](https://www.linkedin.com/in/alokothro/)

Built for the **OKC Thunder Software Engineer Internship Technical Assessment**

---

## 📄 License

This project was created for the OKC Thunder internship technical assessment.
