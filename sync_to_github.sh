#!/bin/bash
#
# Sync Production → GitHub
# Run this script to push latest changes to GitHub
#

set -e

PROD_DIR="/home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker"
REPO_DIR="/home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker-clean"

echo "📦 Syncing production → GitHub..."

# Files to sync (exclude database, logs, cache)
FILES_TO_SYNC=(
    "weather_tracker.py"
    "betting.py"
    "analyze.py"
    "dashboard.py"
    "scrapers_polish.py"
    "scrapers_playwright.py"
    "setup_cron.sh"
    "setup_dashboard.sh"
    "setup_dashboard_simple.sh"
    "queries.sql"
    "README.md"
    "BETTING_GUIDE.md"
    "POLISH_MODELS.md"
    "QUICKSTART.md"
    "DASHBOARD_ACCESS.md"
    "GITHUB_SETUP.md"
    ".gitignore"
)

# Directories to sync
DIRS_TO_SYNC=(
    "infra"
)

# Copy files
for file in "${FILES_TO_SYNC[@]}"; do
    if [ -f "$PROD_DIR/$file" ]; then
        cp "$PROD_DIR/$file" "$REPO_DIR/$file"
        echo "  ✓ $file"
    fi
done

# Copy directories
for dir in "${DIRS_TO_SYNC[@]}"; do
    if [ -d "$PROD_DIR/$dir" ]; then
        cp -r "$PROD_DIR/$dir" "$REPO_DIR/"
        echo "  ✓ $dir/"
    fi
done

# Commit and push
cd "$REPO_DIR"

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "sync: Update from production server $(date +'%Y-%m-%d %H:%M')"
    git push origin main
    echo ""
    echo "✅ Pushed to GitHub: https://github.com/pzawadz/weather-forecast-tracker"
else
    echo ""
    echo "✅ No changes to push"
fi
