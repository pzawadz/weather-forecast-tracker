#!/bin/bash
#
# Setup cron jobs for weather forecast tracker
#

PROJECT_DIR="/home/ubuntu/.openclaw/workspace/projekty/weather-forecast-tracker"
CRON_USER=$(whoami)

echo "Setting up cron jobs for weather forecast tracker..."
echo "Project directory: $PROJECT_DIR"
echo "User: $CRON_USER"

# Create cron jobs
(crontab -l 2>/dev/null; cat <<EOF

# Weather Forecast Tracker - Auto-generated $(date)
# Collect forecasts every 4 hours (6:00, 10:00, 14:00, 18:00, 22:00)
0 6,10,14,18,22 * * * cd $PROJECT_DIR && ./weather_tracker.py forecast >> logs/forecast.log 2>&1

# Collect observations every morning at 8:00 AM
0 8 * * * cd $PROJECT_DIR && ./weather_tracker.py observe >> logs/observe.log 2>&1

# Weekly stats report (Monday 9:00 AM)
0 9 * * 1 cd $PROJECT_DIR && ./weather_tracker.py stats 7 >> logs/stats-weekly.log 2>&1

EOF
) | crontab -

echo "✓ Cron jobs installed"
echo ""
echo "Active cron jobs:"
crontab -l | grep -A 10 "Weather Forecast Tracker"
echo ""
echo "To remove cron jobs: crontab -e (and delete the Weather Forecast Tracker section)"
echo "To view logs:"
echo "  tail -f $PROJECT_DIR/logs/forecast.log"
echo "  tail -f $PROJECT_DIR/logs/observe.log"
