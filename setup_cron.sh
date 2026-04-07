#!/bin/bash
#
# Setup cron jobs for weather forecast tracker + betting recommendations
#

# Auto-detect project directory (run from project root or specify path)
if [ -f "./weather_tracker.py" ]; then
    PROJECT_DIR="$(pwd)"
else
    # Default for production (eu-west-1)
    PROJECT_DIR="/home/ubuntu/weather-forecast-tracker"
fi

CRON_USER=$(whoami)

echo "Setting up cron jobs for weather forecast tracker + betting..."
echo "Project directory: $PROJECT_DIR"
echo "User: $CRON_USER"

# Create cron jobs
(crontab -l 2>/dev/null | grep -v "Weather Forecast Tracker"; cat <<EOF

# Weather Forecast Tracker + Betting - Auto-generated $(date)
# Collect forecasts every 4 hours (24/7 coverage for betting)
0 */4 * * * cd $PROJECT_DIR && ./weather_tracker.py forecast >> logs/forecast.log 2>&1

# Collect observations every morning at 8:00 AM
0 8 * * * cd $PROJECT_DIR && ./weather_tracker.py observe >> logs/observe.log 2>&1

# Generate betting card before peak betting hours (8am, 2pm, 8pm)
0 8,14,20 * * * cd $PROJECT_DIR && ./betting.py card >> logs/betting.log 2>&1

# Weekly stats report (Monday 9:00 AM)
0 9 * * 1 cd $PROJECT_DIR && ./analyze.py summary 7 >> logs/stats-weekly.log 2>&1

EOF
) | crontab -

echo "✓ Cron jobs installed"
echo ""
echo "Schedule:"
echo "  - Forecasts: Every 4 hours (0, 4, 8, 12, 16, 20)"
echo "  - Observations: Daily at 8:00 AM"
echo "  - Betting card: 3x daily (8am, 2pm, 8pm)"
echo "  - Stats report: Weekly (Monday 9am)"
echo ""
echo "Active cron jobs:"
crontab -l | grep -A 15 "Weather Forecast Tracker"
echo ""
echo "To remove cron jobs: crontab -e (and delete the Weather Forecast Tracker section)"
echo ""
echo "Logs:"
echo "  tail -f $PROJECT_DIR/logs/forecast.log"
echo "  tail -f $PROJECT_DIR/logs/betting.log"
echo "  tail -f $PROJECT_DIR/logs/observe.log"

