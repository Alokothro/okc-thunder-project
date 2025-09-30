# Local Development Setup Guide

## Prerequisites

### Required Software
- **Node.js 16.x.x** (NOT Node 18+ or 22+) - Angular 12 compatibility requirement
- **Python 3.10.x**
- **PostgreSQL 14+**

### Important: Node Version

This project uses Angular 12, which **requires Node 16**. If you have Node 18+ or 22+, you'll encounter build errors.

#### Install Node 16 using nvm (Recommended)

```bash
# Install nvm (if not installed)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal or source your profile
source ~/.zshrc  # or ~/.bashrc

# Install and use Node 16
nvm install 16
nvm use 16

# Verify version
node --version  # Should show v16.x.x
```

## Database Setup

1. **Install PostgreSQL** from https://www.postgresql.org/download/

2. **Create Database and User:**
```bash
createuser okcapplicant --createdb
createdb okc
psql okc
```

3. **Grant Permissions (in psql):**
```sql
CREATE SCHEMA app;
ALTER USER okcapplicant WITH PASSWORD 'thunder';
GRANT ALL ON SCHEMA app TO okcapplicant;
\q
```

## Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (if needed)
python manage.py migrate

# Load data (if not already loaded)
python scripts/load_data.py

# Start backend server
python manage.py runserver

# Backend will run on http://localhost:8000
```

## Frontend Setup

**IMPORTANT: Make sure you're using Node 16!**

```bash
# Navigate to frontend directory
cd frontend

# Verify Node version
node --version  # Must be 16.x.x

# Install dependencies
npm install --force

# Start frontend server
npm start

# Frontend will run on http://localhost:4200
```

## Common Issues

### Issue: "Cannot GET /" or compilation errors

**Cause:** Using Node 18+ or Node 22+ instead of Node 16

**Solution:** Switch to Node 16 using nvm:
```bash
nvm use 16
npm start
```

### Issue: OpenSSL error on newer Node versions

If you must use Node 18+, add this workaround:
```bash
NODE_OPTIONS="--openssl-legacy-provider" npm start
```

However, Node 16 is still recommended.

### Issue: Module not found errors (d3, chart.js)

**Solution:** Reinstall dependencies:
```bash
rm -rf node_modules package-lock.json
npm install --force
```

## Testing the Application

### Backend API Test
```bash
curl http://localhost:8000/api/v1/playerSummary/1
```

Should return JSON data for player ID 1.

### Frontend
Open browser to http://localhost:4200

You should see the OKC Technical Assessment interface.

## Production URLs

The application is deployed and running at:
- **Frontend:** https://frontend-production-214a.up.railway.app
- **Backend:** https://backend-production-af17.up.railway.app

## Need Help?

If you encounter issues:
1. Verify Node version is 16.x.x: `node --version`
2. Verify Python version is 3.10.x: `python --version`
3. Check PostgreSQL is running: `psql okc -c "SELECT 1;"`
4. Review error logs in terminal output
