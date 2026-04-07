# Weather Forecast Tracker - Production Setup

## Cron Configuration

**CRITICAL:** Always `cd` into project directory before running scripts!

Without `cd`, cron runs from `$HOME` and creates database in wrong location:
- ❌ Wrong: `/home/ubuntu/weather_forecasts.db` (cron default)
- ✅ Correct: `/home/ubuntu/weather-forecast-tracker/weather_forecasts.db`

### Correct Crontab

```bash
# Weather Forecast Tracker
0 */4 * * * cd /home/ubuntu/weather-forecast-tracker && ./weather_tracker.py forecast >> logs/forecast.log 2>&1
0 8 * * * cd /home/ubuntu/weather-forecast-tracker && ./weather_tracker.py observe >> logs/observe.log 2>&1
0 8,14,20 * * * cd /home/ubuntu/weather-forecast-tracker && ./betting.py card >> logs/betting.log 2>&1
0 9 * * 1 cd /home/ubuntu/weather-forecast-tracker && ./analyze.py summary 7 >> logs/stats.log 2>&1
```

**Key points:**
1. `cd /home/ubuntu/weather-forecast-tracker &&` before every command
2. Relative paths for logs (`logs/` not `./logs/`)
3. Scripts use relative DB path (`weather_forecasts.db`)

### Install Crontab

```bash
# Edit crontab
crontab -e

# Or install from file
crontab /path/to/crontab_file

# Verify
crontab -l | grep weather
```

### Verify Cron Runs

```bash
# Check syslog
sudo grep "weather_tracker" /var/log/syslog | tail -5

# Check logs
tail -50 /home/ubuntu/weather-forecast-tracker/logs/forecast.log

# Check database
cd /home/ubuntu/weather-forecast-tracker
python3 -c "import sqlite3; c = sqlite3.connect('weather_forecasts.db'); print(c.execute('SELECT COUNT(*) FROM forecasts').fetchone()[0])"
```

### Troubleshooting

**Problem:** Dashboard shows "No forecast data available"

**Check 1:** Are there multiple DB files?
```bash
find /home/ubuntu -name "weather_forecasts.db"
```

Should only be ONE: `/home/ubuntu/weather-forecast-tracker/weather_forecasts.db`

**Check 2:** Cron working directory?
```bash
crontab -l | grep forecast
# Must have: cd /home/ubuntu/weather-forecast-tracker &&
```

**Check 3:** Database has recent data?
```bash
cd /home/ubuntu/weather-forecast-tracker
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('weather_forecasts.db')
c = conn.cursor()
for row in c.execute("SELECT target_date, COUNT(*), MAX(forecast_time) FROM forecasts GROUP BY target_date ORDER BY target_date DESC LIMIT 3"):
    print(f"{row[0]}: {row[1]} forecasts (last: {row[2]})")
EOF
```

**Fix:** If multiple DBs exist:
```bash
# Backup wrong DB
mv /home/ubuntu/weather_forecasts.db /home/ubuntu/weather_forecasts.db.backup

# Fix cron (add cd)
crontab -e

# Restart dashboard
sudo systemctl restart weather-dashboard
```

---

## Production Checklist

- [ ] Cron jobs have `cd` before commands
- [ ] Only one `weather_forecasts.db` exists
- [ ] DB location: `/home/ubuntu/weather-forecast-tracker/weather_forecasts.db`
- [ ] Dashboard service uses correct working directory
- [ ] Logs are being written to `/home/ubuntu/weather-forecast-tracker/logs/`
- [ ] Cron runs successfully every 4 hours
- [ ] Dashboard shows current forecast data

---

## Files

- `setup_cron.sh` - Install cron jobs (needs updating with `cd`)
- `PRODUCTION.md` - This file
